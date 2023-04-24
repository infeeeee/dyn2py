from __future__ import annotations
import argparse
import pathlib


LOGLEVELS = ["HEADLESS", "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
DEFAULT_LOGLEVEL = "INFO"
FILTERS = ["py", "dyn"]


class Options(argparse.Namespace):
    """Class for options for running a conversion like from the command line"""

    def __init__(
        self,
        source: list[pathlib.Path | str] = [],
        loglevel: str = DEFAULT_LOGLEVEL,
        dry_run: bool = False,
        force: bool = False,
        backup: bool = False,
        filter: str = "",
        update: bool = False,
        python_folder: pathlib.Path | str | None = None
    ) -> None:
        """Generate an option object for running it like from the command line

        Args:
            source (list[pathlib.Path  |  str], optional): List of files to run on. Defaults to [].
            loglevel (str, optional): Log level. Defaults to DEFAULT_LOGLEVEL.
            dry_run (bool, optional): Dry run, do not save files. Defaults to False.
            force (bool, optional): Overwrite files, even if they are older. Defaults to False.
            backup (bool, optional): Create backup of modified files. Defaults to False.
            filter (str, optional): 'dyn' or 'py' file filter for running on folders. Defaults to "".
            update (bool, optional): Update mode, like inverse on Dynamo files. Defaults to False.
            python_folder (pathlib.Path | str | None, optional): Path to export python files to, or import from there. Defaults to None.
        """

        self.source = []
        for s in source:
            if isinstance(s, str):
                self.source.append(pathlib.Path(s))
            else:
                self.source.append(s)

        self.loglevel = self.sanitize_option_string("loglevel", loglevel)
        self.dry_run = dry_run
        self.force = force
        self.backup = backup
        self.filter = self.sanitize_option_string("filter", filter)
        self.update = update

        if isinstance(python_folder, str):
            self.python_folder = pathlib.Path(python_folder)
        else:
            self.python_folder = python_folder

    @staticmethod
    def sanitize_option_string(arg: str, value: str) -> str:
        """Sanitize string option values

        Args:
            arg (str): The name of the argument
            value (str): The value

        Raises:
            ValueError: if the value is invalid

        Returns:
            str: The correct string
        """

        if arg == "loglevel":
            if value.upper() in LOGLEVELS:
                sanitized_value = value.upper()
            else:
                raise ValueError("Invalid loglevel!")
        elif arg == "filter":
            if not value or value in FILTERS:
                sanitized_value = value
            else:
                raise ValueError("Invalid filter!")
        else:
            sanitized_value = value

        return sanitized_value

    @classmethod
    def from_kwargs(cls, **kwargs) -> Options:
        """Initialize an Options object from kwargs

        Returns:
            Options: The initialized object
        """
        o = cls()
        for key, value in kwargs.items():
            if isinstance(value, str):
                value = cls.sanitize_option_string(key, value)
            setattr(o, key, value)
        return o
