from pathlib import Path

from fluent.runtime import FluentLocalization, FluentResourceLoader


def get_fluent_localization() -> FluentLocalization:
    """
    A helper function to create a FluentLocalization object
    with the necessary configuration.
    Returns:
        A FluentLocalization object.
    """

    # Check if the required files and directories
    locale_dir = Path(__file__).parent.joinpath("l10n")
    if not locale_dir.exists():
        error = "'l10n' directory not found"
        raise FileNotFoundError(error)
    if not locale_dir.is_dir():
        error = "'l10n' is not a directory"
        raise NotADirectoryError(error)
    locale_file = Path(locale_dir, "locale.ftl")
    if not locale_file.exists():
        error = "locale.txt file not found"
        raise FileNotFoundError(error)

    # Create a FluentResourceLoader object
    l10n_loader = FluentResourceLoader(
        str(locale_file.absolute()),
    )
    return FluentLocalization(
        locales=["ru"],
        resource_ids=[str(locale_file.absolute())],
        resource_loader=l10n_loader
    )