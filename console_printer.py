class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'  # Resets the color to default
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ConsolePrinter:
    @staticmethod
    def print_message(message, color=None):
        """Prints a message with optional color."""
        print(f"{color}{message}{Colors.ENDC}" if color else message)

    @staticmethod
    def info(message):
        ConsolePrinter.print_message(message, Colors.OKGREEN)

    @staticmethod
    def warning(message):
        ConsolePrinter.print_message(message, Colors.WARNING)

    @staticmethod
    def error(message):
        ConsolePrinter.print_message(message, Colors.FAIL)

    @staticmethod
    def chat(message):
        ConsolePrinter.print_message(message, Colors.OKBLUE)