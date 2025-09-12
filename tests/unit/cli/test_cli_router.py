"""
Unit tests for CLIRouter.

Tests CLI routing, argument parsing, and command delegation
without breaking existing functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from argparse import Namespace

from form16x.form16_parser.cli import CLIRouter


class TestCLIRouter(unittest.TestCase):
    """Test cases for CLIRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = CLIRouter()
    
    def test_cli_router_initialization(self):
        """Test CLIRouter initialization."""
        self.assertIsNotNone(self.router.ui)
        self.assertIsNotNone(self.router.ascii_art)
        self.assertIsNotNone(self.router.commands)
        
        # Verify all expected commands are registered
        expected_commands = ['optimize', 'extract', 'consolidate', 'batch']
        for cmd in expected_commands:
            self.assertIn(cmd, self.router.commands)
    
    def test_create_parser_structure(self):
        """Test argument parser creation and structure."""
        parser = self.router.create_parser()
        
        self.assertEqual(parser.prog, "form16x")
        self.assertIn("Professional Form16 Processing", parser.description)
        
        # Test version argument
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                try:
                    parser.parse_args(['--version'])
                except SystemExit:
                    pass
                mock_print.assert_called()
    
    def test_extract_command_parser(self):
        """Test extract command argument parsing."""
        parser = self.router.create_parser()
        
        # Test valid extract command
        args = parser.parse_args(['extract', 'json', '/test/form16.pdf'])
        self.assertEqual(args.command, 'extract')
        self.assertEqual(args.format, 'json')
        self.assertEqual(str(args.file), '/test/form16.pdf')
        
        # Test extract with additional options
        args = parser.parse_args([
            'extract', 'json', '/test/form16.pdf', 
            '--calculate-tax', '--tax-regime', 'both', '--verbose'
        ])
        self.assertTrue(args.calculate_tax)
        self.assertEqual(args.tax_regime, 'both')
        self.assertTrue(args.verbose)
    
    def test_optimize_command_parser(self):
        """Test optimize command argument parsing."""
        parser = self.router.create_parser()
        
        # Test basic optimize command
        args = parser.parse_args(['optimize', '/test/form16.pdf'])
        self.assertEqual(args.command, 'optimize')
        self.assertEqual(str(args.file), '/test/form16.pdf')
        
        # Test optimize with options
        args = parser.parse_args([
            'optimize', '/test/form16.pdf', 
            '--suggestions-only', '--target-savings', '50000', '--interactive'
        ])
        self.assertTrue(args.suggestions_only)
        self.assertEqual(args.target_savings, 50000)
        self.assertTrue(args.interactive)
    
    def test_consolidate_command_parser(self):
        """Test consolidate command argument parsing."""
        parser = self.router.create_parser()
        
        args = parser.parse_args([
            'consolidate', 
            '--files', '/test/form16_1.pdf', '/test/form16_2.pdf',
            '--calculate-tax'
        ])
        self.assertEqual(args.command, 'consolidate')
        self.assertEqual(len(args.files), 2)
        self.assertTrue(args.calculate_tax)
    
    def test_batch_command_parser(self):
        """Test batch command argument parsing."""
        parser = self.router.create_parser()
        
        args = parser.parse_args([
            'batch', 
            '--input-dir', '/test/input',
            '--output-dir', '/test/output',
            '--parallel', '8'
        ])
        self.assertEqual(args.command, 'batch')
        self.assertEqual(str(args.input_dir), '/test/input')
        self.assertEqual(str(args.output_dir), '/test/output')
        self.assertEqual(args.parallel, 8)
    
    def test_common_arguments_parsing(self):
        """Test common arguments are available for all commands."""
        parser = self.router.create_parser()
        
        # Test common args with extract command
        args = parser.parse_args([
            'extract', 'json', '/test/form16.pdf', 
            '--verbose', '--dummy', '--config', '/test/config.yaml'
        ])
        self.assertTrue(args.verbose)
        self.assertTrue(args.dummy)
        self.assertEqual(str(args.config), '/test/config.yaml')
    
    @patch('form16x.form16_parser.cli.OptimizeCommand')
    def test_route_command_optimize(self, mock_optimize_command):
        """Test routing to optimize command."""
        mock_command_instance = Mock()
        mock_command_instance.execute.return_value = 0
        mock_optimize_command.return_value = mock_command_instance
        
        args = Namespace(command='optimize', file='test.pdf')
        
        with patch.object(self.router, '_display_startup_logo'):
            result = self.router.route_command(args)
            
            self.assertEqual(result, 0)
            mock_optimize_command.assert_called_once()
            mock_command_instance.execute.assert_called_once_with(args)
    
    @patch('form16x.form16_parser.cli.ExtractCommand')
    def test_route_command_extract(self, mock_extract_command):
        """Test routing to extract command."""
        mock_command_instance = Mock()
        mock_command_instance.execute.return_value = 0
        mock_extract_command.return_value = mock_command_instance
        
        args = Namespace(command='extract', format='json', file='test.pdf')
        
        with patch.object(self.router, '_display_startup_logo'):
            result = self.router.route_command(args)
            
            self.assertEqual(result, 0)
            mock_extract_command.assert_called_once()
            mock_command_instance.execute.assert_called_once_with(args)
    
    def test_route_command_no_command(self):
        """Test routing with no command specified."""
        args = Namespace(command=None)
        
        with patch.object(self.router, '_display_startup_logo'):
            with patch.object(self.router.ui.console, 'print') as mock_print:
                result = self.router.route_command(args)
                
                self.assertEqual(result, 1)
                mock_print.assert_called()
    
    def test_route_command_unknown_command(self):
        """Test routing with unknown command."""
        args = Namespace(command='unknown')
        
        with patch.object(self.router, '_display_startup_logo'):
            with patch.object(self.router.ui.console, 'print') as mock_print:
                result = self.router.route_command(args)
                
                self.assertEqual(result, 1)
                mock_print.assert_called()
    
    @patch('form16x.form16_parser.cli.OptimizeCommand')
    def test_route_command_exception_handling(self, mock_optimize_command):
        """Test command exception handling."""
        mock_command_instance = Mock()
        mock_command_instance.execute.side_effect = Exception("Command failed")
        mock_optimize_command.return_value = mock_command_instance
        
        args = Namespace(command='optimize', file='test.pdf')
        
        with patch.object(self.router, '_display_startup_logo'):
            # Should not raise exception, should handle gracefully
            result = self.router.route_command(args)
            
            # Command should still be called even if it fails
            mock_command_instance.execute.assert_called_once()
    
    def test_display_startup_logo(self):
        """Test startup logo display."""
        with patch.object(self.router.ascii_art, 'display_startup_logo') as mock_logo:
            self.router._display_startup_logo()
            mock_logo.assert_called_once_with(option=1, show_tagline=True)
    
    @patch('sys.argv', ['form16x', 'extract', 'json', '/test/form16.pdf'])
    @patch('form16x.form16_parser.cli.ExtractCommand')
    def test_run_method_success(self, mock_extract_command):
        """Test successful run method execution."""
        mock_command_instance = Mock()
        mock_command_instance.execute.return_value = 0
        mock_extract_command.return_value = mock_command_instance
        
        with patch.object(self.router, '_display_startup_logo'):
            result = self.router.run()
            
            self.assertEqual(result, 0)
    
    def test_run_method_keyboard_interrupt(self):
        """Test run method handling KeyboardInterrupt."""
        with patch.object(self.router, 'create_parser') as mock_parser:
            mock_parser.side_effect = KeyboardInterrupt()
            
            with patch.object(self.router.ui.console, 'print') as mock_print:
                result = self.router.run()
                
                self.assertEqual(result, 130)
                mock_print.assert_called()
    
    def test_run_method_general_exception(self):
        """Test run method handling general exceptions."""
        with patch.object(self.router, 'create_parser') as mock_parser:
            mock_parser.side_effect = Exception("Unexpected error")
            
            with patch.object(self.router.ui.console, 'print') as mock_print:
                result = self.router.run()
                
                self.assertEqual(result, 1)
                mock_print.assert_called()
    
    def test_run_with_custom_argv(self):
        """Test run method with custom argv."""
        custom_argv = ['extract', 'json', '/custom/form16.pdf']
        
        with patch('form16x.form16_parser.cli.ExtractCommand') as mock_extract_command:
            mock_command_instance = Mock()
            mock_command_instance.execute.return_value = 0
            mock_extract_command.return_value = mock_command_instance
            
            with patch.object(self.router, '_display_startup_logo'):
                result = self.router.run(custom_argv)
                
                self.assertEqual(result, 0)
    
    def test_parser_format_choices(self):
        """Test that format choices are correctly defined."""
        parser = self.router.create_parser()
        
        # Extract command should have correct format choices
        with self.assertRaises(SystemExit):
            # Invalid format should cause parser error
            parser.parse_args(['extract', 'invalid_format', '/test/form16.pdf'])
    
    def test_parser_tax_regime_choices(self):
        """Test that tax regime choices are correctly defined."""
        parser = self.router.create_parser()
        
        args = parser.parse_args(['extract', 'json', '/test/form16.pdf', '--tax-regime', 'old'])
        self.assertEqual(args.tax_regime, 'old')
        
        args = parser.parse_args(['extract', 'json', '/test/form16.pdf', '--tax-regime', 'new'])
        self.assertEqual(args.tax_regime, 'new')
        
        args = parser.parse_args(['extract', 'json', '/test/form16.pdf', '--tax-regime', 'both'])
        self.assertEqual(args.tax_regime, 'both')
    
    def test_all_commands_have_common_args(self):
        """Test that all commands support common arguments."""
        parser = self.router.create_parser()
        common_args = ['--verbose', '--dummy', '--config', '/test/config.yaml']
        
        commands_to_test = [
            ['extract', 'json', '/test/form16.pdf'],
            ['optimize', '/test/form16.pdf'],
            ['consolidate', '--files', '/test/form16.pdf'],
            ['batch', '--input-dir', '/test/input', '--output-dir', '/test/output']
        ]
        
        for base_cmd in commands_to_test:
            args = parser.parse_args(base_cmd + common_args)
            self.assertTrue(args.verbose)
            self.assertTrue(args.dummy)
            self.assertEqual(str(args.config), '/test/config.yaml')


if __name__ == '__main__':
    unittest.main()