"""
Professional ASCII Art for Form16x CLI

Provides various ASCII art options for the CLI interface with professional presentation.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
import time

class CLIAsciiArt:
    """Professional ASCII art generator for CLI"""
    
    def __init__(self):
        self.console = Console()
    
    @staticmethod
    def get_form16x_logo_option_1():
        """Modern geometric style with clean professional appearance"""
        return """
╭─────────────────────────────────────────────────────────────╮
│  ███████╗ ██████╗ ██████╗ ███╗   ███╗  ██╗ ██████╗ ██╗  ██╗ │
│  ██╔════╝██╔═══██╗██╔══██╗████╗ ████║ ███║██╔════╝ ╚██╗██╔╝ │
│  █████╗  ██║   ██║██████╔╝██╔████╔██║ ╚██║███████╗  ╚███╔╝  │
│  ██╔══╝  ██║   ██║██╔══██╗██║╚██╔╝██║  ██║██╔═══██╗ ██╔██╗  │
│  ██║     ╚██████╔╝██║  ██║██║ ╚═╝ ██║  ██║╚██████╔╝██╔╝ ██╗ │
│  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ │
╰─────────────────────────────────────────────────────────────╯
"""
    
    @staticmethod
    def get_form16x_logo_option_2():
        """Clean minimalist style - inspired by modern CLIs"""
        return """
┌───────────────────────────────────────────────────┐
│  ╔═══╗╔═══╗╔═══╗╔═╗╔═╗  ╔═╗╔═══╗╔═══╗╔╗  ╔╗      │
│  ║╔══╝║╔═╗║║╔═╗║║║╚╝║║ ╔╝╚╗║╔═╗║║╔══╝╚╝╔╗╚╝      │  
│  ║╚══╗║║ ║║║╚═╝║║╔╗╔╗║ ╚╗╔╝║╚═╝║║╚══╗  ╚╝        │
│  ║╔══╝║║ ║║║╔══╝║║║║║║  ║║ ║╔══╝║╔══╝╔╗  ╔╗      │
│  ║║   ║╚═╝║║║   ║║║║║║ ╔╝╚╗║║   ║╚══╗╚╝╔╗╚╝      │
│  ╚╝   ╚═══╝╚╝   ╚╝╚╝╚╝ ╚══╝╚╝   ╚═══╝  ╚╝        │
└───────────────────────────────────────────────────┘
"""
    
    @staticmethod
    def get_form16x_logo_option_3():
        """3D block style - bold and professional"""
        return """
██████████████████████████████████████████████████
█                                                █
█  ████████  ████████  ████████  ████████   █████ █
█  ██       ██    ██  ██    ██  ██  ██  ██     ██ █
█  ████████ ██    ██  ████████  ██  ██  ██ ██████ █
█  ██       ██    ██  ██  ██    ██      ██    ██  █
█  ██        ████████  ██   ██  ██  ██  ██ ██████ █
█                                                █
██████████████████████████████████████████████████
"""
    
    @staticmethod
    def get_form16x_logo_option_4():
        """Corporate professional style with clear lettering"""
        return """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ██████  ████   ██████  ██████   ██  ███████ ██   ██   ║
║   ██      ██  ██ ██   ██ ██  ██  ███  ██      ██   ██   ║
║   █████   ██  ██ ██████  ██████   ██  █████    █████    ║
║   ██      ██  ██ ██   ██ ██  ██   ██  ██      ██   ██   ║
║   ██      ████   ██   ██ ██   ██ ████ ███████ ██   ██   ║
║                                                          ║
║              Professional Tax Document Parser            ║
╚══════════════════════════════════════════════════════════╝
"""
    
    @staticmethod
    def get_form16x_logo_option_5():
        """Modern tech style - inspired by Gemini"""
        return """
    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   ▐                                                     ▌
   ▐  ██████   ████   █████   █████    █   ██████   ██   ▌
   ▐  █       █    █  █    █  █    █  ██   █       ██    ▌
   ▐  █████   █    █  █████   █████   █ █  █████    █    ▌
   ▐  █       █    █  █  █    █  █       █  █      ██    ▌
   ▐  █        ████   █   █   █   █   ████  ██████   █    ▌
   ▐                                                     ▌
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""
    
    def display_startup_logo(self, option: int = 1, show_tagline: bool = True):
        """Display the startup logo with optional tagline"""
        
        # Clear screen effect
        self.console.clear()
        
        # Get the selected logo
        logos = {
            1: self.get_form16x_logo_option_1(),
            2: self.get_form16x_logo_option_2(),
            3: self.get_form16x_logo_option_3(),
            4: self.get_form16x_logo_option_4(),
            5: self.get_form16x_logo_option_5()
        }
        
        logo = logos.get(option, logos[1])
        
        # Display logo with colors
        if option == 1:
            # Modern geometric - cyan and blue
            logo_text = Text(logo, style="bold cyan")
        elif option == 2:
            # Clean minimalist - green
            logo_text = Text(logo, style="bold green")
        elif option == 3:
            # 3D block - magenta
            logo_text = Text(logo, style="bold magenta")
        elif option == 4:
            # Corporate - blue
            logo_text = Text(logo, style="bold blue")
        elif option == 5:
            # Modern tech - bright yellow
            logo_text = Text(logo, style="bold bright_yellow")
        
        # Center the logo
        self.console.print(Align.center(logo_text))
        
        # Add tagline if requested
        if show_tagline:
            taglines = {
                1: "Professional Form16 Processing & Tax Calculation",
                2: "Smart Tax Document Parser",
                3: "Enterprise Tax Processing Solution",
                4: "Advanced Form16 Analytics Platform",
                5: "Professional Tax Document Intelligence"
            }
            
            tagline = taglines.get(option, taglines[1])
            tagline_text = Text(tagline, style="italic dim white")
            self.console.print(Align.center(tagline_text))
            self.console.print()
        
        # Animation effect
        time.sleep(0.8)
        
        # Version info
        version_text = Text("v1.0.0", style="dim white")
        self.console.print(Align.center(version_text))
        self.console.print("\n")
    
    def display_command_header(self, command_name: str, description: str = ""):
        """Display header for specific commands"""
        
        # Create a nice header box
        header_content = f"[bold cyan]{command_name.upper()}[/bold cyan]"
        if description:
            header_content += f"\n[dim white]{description}[/dim white]"
        
        header_panel = Panel(
            Align.center(header_content),
            border_style="cyan",
            width=60
        )
        
        self.console.print(header_panel)
        self.console.print()
    
    def display_processing_separator(self):
        """Display a nice separator before processing starts"""
        separator = "═" * 60
        separator_text = Text(separator, style="dim blue")
        self.console.print(Align.center(separator_text))
        self.console.print()
    
    def show_all_logo_options(self):
        """Display all logo options for selection"""
        self.console.print("[bold yellow]Form16x CLI Logo Options[/bold yellow]\n")
        
        options = [
            ("Option 1: Modern Geometric", "Bold and clean professional design"),
            ("Option 2: Clean Minimalist", "Simple and professional"),
            ("Option 3: 3D Block Style", "Bold and impactful"),
            ("Option 4: Corporate Style", "Professional business look"),
            ("Option 5: Modern Tech Style", "Futuristic and technical appearance")
        ]
        
        for i, (title, desc) in enumerate(options, 1):
            self.console.print(f"[bold cyan]{title}[/bold cyan]")
            self.console.print(f"[dim]{desc}[/dim]")
            
            # Show the actual logo
            logo_method = getattr(self, f'get_form16x_logo_option_{i}')
            logo_text = Text(logo_method(), style="green" if i % 2 == 0 else "cyan")
            self.console.print(logo_text)
            self.console.print("─" * 50)
            self.console.print()


def demo_all_logos():
    """Demo function to show all logo options"""
    art = CLIAsciiArt()
    
    for i in range(1, 6):
        art.console.clear()
        art.console.print(f"[bold yellow]Displaying Option {i}:[/bold yellow]\n")
        art.display_startup_logo(i, show_tagline=True)
        time.sleep(2)
    
    # Show all options together
    art.console.clear()
    art.show_all_logo_options()


if __name__ == "__main__":
    demo_all_logos()