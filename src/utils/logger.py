import datetime

class Logger:
    # Define color codes as class constants
    COLORS = {
        "ERROR": "\033[91m",   # Red
        "WARNING": "\033[93m", # Yellow
        "INFO": "",            # Default terminal color
        "DEBUG": "\033[94m"    # Blue
    }
    
    def __init__(self, type: str, use_colors_in_file: bool = False):
        self.type = type
        self.use_colors_in_file = use_colors_in_file
        if self.type == "exchange":
            self.file_path = "logs/exchanges/exchange.log"  
        elif self.type == "arbitrage":
            self.file_path = "logs/arbitrage/arbitrage.log"
        elif self.type == "trades":
            self.file_path = "logs/trades/trades.log"
        elif self.type == "main":
            self.file_path = "logs/main/main.log"
        self.clear_log()
    
    # # # # # # # # # # 
    # General methods # 
    # # # # # # # # # # 

    def log(self, message: str):
        try:
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Append to log file
            with open(self.file_path, "a") as log_file:
                log_file.write(f"{message}\n")
        except Exception as e:
            print(f"\033[91m[LOGGING ERROR] Failed to write to log file: {str(e)}\033[0m")

    def clear_log(self):
        try:
            with open(self.file_path, "w") as log_file:
                log_file.truncate(0)
        except Exception as e:
            print(f"\033[91m[LOGGING ERROR] Failed to clear log file: {str(e)}\033[0m")

    def _log_message(self, level: str, message: str):
        """
        General logging method that handles formatting and output based on log level
        
        Args:
            level: The log level (ERROR, WARNING, INFO, DEBUG)
            message: The message to log
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get color code for this level
        color_code = self.COLORS.get(level, "")
        reset_code = "\033[0m" if color_code else ""
        
        if color_code:
            colored_message = f"[{timestamp}] [{color_code}{level}{reset_code}] {message}"
        else:
            colored_message = f"[{timestamp}] [{level}] {message}"
        
        plain_message = f"[{timestamp}] [{level}] {message}"
        
        print(colored_message)
        
        self.log(colored_message if self.use_colors_in_file else plain_message)

    # # # # # # # # # # # # # # # 
    #  Specific logging methods #  
    # # # # # # # # # # # # # # # 

    def error(self, message: str):
        """
        Log an error message to both file and terminal.
        
        Args:
            message: The error message to log
        """
        self._log_message("ERROR", message)

    def warning(self, message: str):
        """
        Log a warning message to both file and terminal.
        
        Args:
            message: The warning message to log
        """
        self._log_message("WARNING", message)
    
    def info(self, message: str):
        """
        Log an info message to both file and terminal.
        
        Args:
            message: The info message to log
        """
        self._log_message("INFO", message)
    
    def debug(self, message: str):
        """
        Log a debug message to both file and terminal.
        
        Args:
            message: The debug message to log
        """
        self._log_message("DEBUG", message)
        

# Example usage
# To use with colors in log file: logger = Logger("exchange", use_colors_in_file=True)
# To use without colors in log file (default): logger = Logger("exchange")
# logger = Logger("exchange")
# logger.error("Test error")
# logger.warning("Test warning")
# logger.info("Test info")
# logger.debug("Test debug")
# logger.clear_log()
