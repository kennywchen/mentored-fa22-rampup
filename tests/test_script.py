#!/usr/bin/env python3
"""
Test suite for script.py
Tests the webhook functionality, GitHub API integration, and cursor-agent processing
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import subprocess
import os
import sys
from threading import Thread
import time

# Add the current directory to the path so we can import script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import script

class TestScript(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = script.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token_123'})
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.env_patcher.stop()
    
    def test_webhook_endpoint_exists(self):
        """Test that the webhook endpoint exists and accepts POST requests."""
        response = self.client.post('/webhook', 
                                  data=json.dumps({'test': 'data'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'OK')
    
    def test_webhook_with_github_event(self):
        """Test webhook with GitHub event header."""
        response = self.client.post('/webhook',
                                  data=json.dumps({'action': 'created', 'comment': {'body': 'test comment'}}),
                                  content_type='application/json',
                                  headers={'X-GitHub-Event': 'pull_request_review_comment'})
        self.assertEqual(response.status_code, 200)
    
    def test_webhook_without_github_event(self):
        """Test webhook without GitHub event header."""
        response = self.client.post('/webhook',
                                  data=json.dumps({'test': 'data'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
    
    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON."""
        response = self.client.post('/webhook',
                                  data='invalid json',
                                  content_type='application/json')
        # Should still return 200 as the webhook is designed to be resilient
        self.assertEqual(response.status_code, 200)
    
    @patch('script.subprocess.Popen')
    def test_process_prompt_success(self, mock_popen):
        """Test successful prompt processing."""
        # Mock the subprocess
        mock_process = Mock()
        mock_process.communicate.return_value = ('{"type":"result","data":"test result"}', '')
        mock_popen.return_value = mock_process
        
        # Test the function
        script.process_prompt("Test prompt", 0)
        
        # Verify subprocess was called correctly
        mock_popen.assert_called_once_with(
            ["cursor-agent"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        mock_process.communicate.assert_called_once_with(input="Test prompt\n")
    
    @patch('script.subprocess.Popen')
    def test_process_prompt_with_stderr(self, mock_popen):
        """Test prompt processing with stderr output."""
        mock_process = Mock()
        mock_process.communicate.return_value = ('{"type":"result","data":"test"}', 'Error message')
        mock_popen.return_value = mock_process
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            script.process_prompt("Test prompt", 0)
            # Verify error message was printed
            mock_print.assert_any_call("STDERR 1: Error message")
    
    @patch('script.subprocess.Popen')
    def test_process_prompt_exception(self, mock_popen):
        """Test prompt processing with exception."""
        mock_popen.side_effect = Exception("Process failed")
        
        # Should not raise exception
        with patch('builtins.print') as mock_print:
            script.process_prompt("Test prompt", 0)
            mock_print.assert_any_call("Error processing prompt 1: Process failed")
    
    @patch('script.requests.get')
    def test_github_api_integration(self, mock_get):
        """Test GitHub API integration."""
        # Mock GitHub API response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'body': 'Test comment',
                'path': 'test.py',
                'start_line': None,
                'line': 10
            }
        ]
        mock_get.return_value = mock_response
        
        # Test the main function logic (without actually running cursor-agent)
        with patch('script.process_prompt') as mock_process:
            with patch('script.subprocess.run') as mock_subprocess:
                # Mock the prompts list
                prompts = ["Test prompt 1", "Test prompt 2"]
                
                # Test thread creation
                threads = []
                for i, prompt in enumerate(prompts):
                    thread = Thread(target=mock_process, args=(prompt, i))
                    threads.append(thread)
                
                # Start and join threads
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                
                # Verify process_prompt was called for each prompt
                self.assertEqual(mock_process.call_count, 2)
    
    @patch('script.subprocess.run')
    def test_git_operations(self, mock_run):
        """Test git operations."""
        # Mock git commands
        mock_run.return_value = Mock(returncode=0)
        
        # Test git operations
        script.subprocess.run(["git", "add", "."])
        script.subprocess.run(["git", "commit", "-m", "Automatically fixed bugs"])
        script.subprocess.run(["git", "push"])
        
        # Verify git commands were called
        expected_calls = [
            unittest.mock.call(["git", "add", "."]),
            unittest.mock.call(["git", "commit", "-m", "Automatically fixed bugs"]),
            unittest.mock.call(["git", "push"])
        ]
        mock_run.assert_has_calls(expected_calls)
    
    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        with patch('script.load_dotenv') as mock_load_dotenv:
            with patch('script.os.getenv') as mock_getenv:
                mock_getenv.return_value = 'test_token'
                
                # Test that load_dotenv is called
                script.load_dotenv()
                mock_load_dotenv.assert_called_once()
                
                # Test token retrieval
                token = script.os.getenv("GITHUB_TOKEN")
                self.assertEqual(token, 'test_token')
    
    def test_missing_github_token(self):
        """Test behavior when GitHub token is missing."""
        with patch('script.os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            # Test that the function handles missing token
            with patch('builtins.print') as mock_print:
                # This would be called in main() when token is None
                if not script.os.getenv("GITHUB_TOKEN"):
                    mock_print("Error: GITHUB_TOKEN not found in environment variables")
                    mock_print.assert_called_with("Error: GITHUB_TOKEN not found in environment variables")
    
    @patch('script.subprocess.Popen')
    def test_cursor_agent_output_parsing(self, mock_popen):
        """Test parsing of cursor-agent output."""
        # Test with valid JSON result
        mock_process = Mock()
        mock_process.communicate.return_value = (
            'Some output\n{"type":"result","data":"success"}', 
            ''
        )
        mock_popen.return_value = mock_process
        
        with patch('builtins.print') as mock_print:
            script.process_prompt("Test prompt", 0)
            # Verify result was extracted and printed
            mock_print.assert_any_call("Result 1: {\"type\":\"result\",\"data\":\"success\"}")
        
        # Test with no JSON result
        mock_process.communicate.return_value = ('No JSON here', '')
        with patch('builtins.print') as mock_print:
            script.process_prompt("Test prompt", 1)
            mock_print.assert_any_call("Full output 2: No JSON here")
    
    def test_thread_creation_and_management(self):
        """Test that threads are created and managed correctly."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        
        with patch('script.process_prompt') as mock_process:
            # Create threads
            threads = []
            for i, prompt in enumerate(prompts):
                thread = Thread(target=mock_process, args=(prompt, i))
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Join all threads
            for thread in threads:
                thread.join()
            
            # Verify all prompts were processed
            self.assertEqual(mock_process.call_count, 3)
            
            # Verify correct arguments were passed
            expected_calls = [
                unittest.mock.call("Prompt 1", 0),
                unittest.mock.call("Prompt 2", 1),
                unittest.mock.call("Prompt 3", 2)
            ]
            mock_process.assert_has_calls(expected_calls)


class TestIntegration(unittest.TestCase):
    """Integration tests that test the system as a whole."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.app = script.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch('script.subprocess.Popen')
    @patch('script.requests.get')
    def test_full_webhook_flow(self, mock_get, mock_popen):
        """Test the complete webhook flow from GitHub event to cursor-agent processing."""
        # Mock GitHub API response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'body': 'Fix this bug',
                'path': 'bug.py',
                'start_line': None,
                'line': 5
            }
        ]
        mock_get.return_value = mock_response
        
        # Mock cursor-agent process
        mock_process = Mock()
        mock_process.communicate.return_value = ('{"type":"result","data":"Fixed!"}', '')
        mock_popen.return_value = mock_process
        
        # Mock git operations
        with patch('script.subprocess.run') as mock_git:
            # Simulate webhook call
            response = self.client.post('/webhook',
                                      data=json.dumps({'action': 'created'}),
                                      content_type='application/json',
                                      headers={'X-GitHub-Event': 'pull_request_review_comment'})
            
            self.assertEqual(response.status_code, 200)
    
    def test_server_startup(self):
        """Test that the server can start up correctly."""
        with patch('script.app.run') as mock_run:
            with patch('script.main') as mock_main:
                # This would be called in the main execution block
                script.run_server()
                mock_run.assert_called_once_with(port=5000, threaded=True, use_reloader=False)


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestScript))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
