import sys 
from app.command_line_app import CommandLineApp

if __name__ == "__main__":
    CommandLineApp(sys.argv[1:]).run()
