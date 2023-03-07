import argparse
import pathlib


LOGLEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
DEFAULT_LOGLEVEL = "INFO"
FILTERS = ["py", "dyn"]

class Options(argparse.Namespace):
    """Class for options for running a conversion like from the command line"""
    def __init__(
        self,
        source: list[pathlib.Path | str] = [],
        loglevel: str = DEFAULT_LOGLEVEL,
        dry_run: bool = False,
        backup: bool = False,
        filter: str = "",
        update: bool = False,
        python_folder: pathlib.Path | str | None = None
    ) -> None:
        """Generate an option object for running it like from the command line

        Args:
            source (list[pathlib.Path  |  str], optional): List of files to run on. Defaults to [].
            loglevel (str, optional): log level. Defaults to DEFAULT_LOGLEVEL.
            dry_run (bool, optional): If it's a dry run. Defaults to False.
            backup (bool, optional): Create backup of modified files. Defaults to False.
            filter (str, optional): 'dyn' or 'py' file filter for running on folders. Defaults to "".
            update (bool, optional): Update mode, like inverse on Dynamo files. Defaults to False.
            python_folder (pathlib.Path | str | None, optional): Path to export python files to, or import from there. Defaults to None.

        Raises:
            ValueError: If loglevel or filter is invalid
        """

        self.source = []
        for s in source:
            if isinstance(s, str):
                self.source.append(pathlib.Path(s))
            else:
                self.source.append(s)

        if loglevel.upper() in LOGLEVELS:
            self.loglevel = loglevel.upper()
        else:
            raise ValueError

        self.dry_run = dry_run
        self.backup = backup

        if not filter or filter in FILTERS:
            self.filter = filter
        else:
            raise ValueError

        self.update = update

        if isinstance(python_folder, str):
            self.python_folder = pathlib.Path(python_folder)
        else:
            self.python_folder = python_folder

        # super().__init__(
        #     source=self.source,
        #     loglevel=self.loglevel,
        #     dry_run=self.dry_run,
        #     backup=self.backup,
        #     filter=self.filter,
        #     update=self.update,
        #     python_folder=self.python_folder,
        # )



