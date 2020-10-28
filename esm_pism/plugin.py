import os
import sys

from loguru import logger
import xarray as xr

VALID_PISM_COUPLERS = ["ocean", "surface", "atmosphere"]


@logger.catch
def _add_files(coupler_files, config):
    """Adds files to a specific coupler"""
    command_line_args = []
    for file_tag, file_path in coupler_files.items():
        command_line_args.append(f"-{file_tag} {os.path.basename(file_path)}")
        for needed_dict in ["forcing_files", "forcing_sources", "forcing_in_work"]:
            if needed_dict not in config["pism"]:
                config["pism"][needed_dict] = {}
        config["pism"]["forcing_files"][file_tag] = file_tag
        config["pism"]["forcing_sources"][file_tag] = file_path
        config["pism"]["forcing_in_work"][file_tag] = os.path.basename(file_path)
    return command_line_args


@logger.catch
def _add_kv(coupler_key_value, config):
    """Adds kv pairs for a coupler"""
    return [
        f"{key} {value}" if key.startswith("-") else f"-{key} {value}"
        for key, value in coupler_key_value.items()
    ]


@logger.catch
def _add_flags(coupler_flags, config):
    """Adds flags for a coupler"""
    return [f"{flag}" if flag.startswith("-") else f"-{flag}" for flag in coupler_flags]


@logger.catch
def pism_set_couplers(config):
    """

    Parameters
    ----------
    config : dict
        The entire exp config

    Returns
    -------
    config : dict
        The entire exp config
    """
    coupler_dict = config["pism"].get("couplers", {})
    pism_command_line_opts = config["pism"].get("pism_command_line_opts", [])
    command_line_additions = []
    for coupler_type, coupler_spec in coupler_dict.items():
        chosen_couplers = []
        if coupler_type not in VALID_PISM_COUPLERS:
            logger.error(
                f"You can only use {' '.join(VALID_PISM_COUPLERS)} as a coupler type. You had: {coupler_type}!"
            )
            sys.exit(1)
        for coupler_model, coupler_model_opts in coupler_spec.items():
            chosen_couplers.append(coupler_model)
            if coupler_model_opts:  # Not empty:
                if "files" in coupler_model_opts:
                    command_line_args_files_additions = _add_files(
                        coupler_model_opts["files"], config
                    )
                    if command_line_args_files_additions:
                        command_line_additions += command_line_args_files_additions
                if "kv_pairs" in coupler_model_opts:
                    command_line_args_kv_additions = _add_kv(
                        coupler_model_opts["kv_pairs"], config
                    )
                    if command_line_args_kv_additions:
                        command_line_additions += command_line_args_kv_additions
                if "flags" in coupler_model_opts:
                    command_line_args_flags_additions = _add_flags(
                        coupler_model_opts["flags"], config
                    )
                    if command_line_args_flags_additions:
                        command_line_additions += command_line_args_flags_additions
        command_line_additions.append(f"-{coupler_type} " + ",".join(chosen_couplers))
    config["pism"]["pism_command_line_opts"] = (
        pism_command_line_opts + command_line_additions
    )
    return config


@logger.catch
def pism_set_kv_pairs(config):
    """

    Parameters
    ----------
    config : dict
        The entire exp config

    Returns
    -------
    config : dict
        The entire exp config
    """
    kv_pairs = config["pism"].get("kv_pairs", {})
    pism_command_line_opts = config["pism"].get("pism_command_line_opts", [])
    pism_command_line_opts += [
        f"{key} {value}" if key.startswith("-") else f"-{key} {value}"
        for key, value in kv_pairs.items()
    ]
    config["pism"]["pism_command_line_opts"] = pism_command_line_opts
    return config


@logger.catch
def pism_set_flags(config):
    """

    Parameters
    ----------
    config : dict
        The entire exp config

    Returns
    -------
    config : dict
        The entire exp config
    """
    flags = config["pism"].get("flags", [])
    pism_command_line_opts = config["pism"].get("pism_command_line_opts", [])
    pism_command_line_opts += [
        f"{flag}" if flag.startswith("-") else f"-{flag}" for flag in flags
    ]
    config["pism"]["pism_command_line_opts"] = pism_command_line_opts
    return config


@logger.catch
def pism_override_file(config):
    """
    Generates a PISM Overrides file.

    Opens the ``pism_config.nc`` file in your YAML (see below), or uses the
    default found in the model directory under ``share/pism/pism_config.nc``.
    This is used to determine which override keys are valid. A new file is
    written which is used during your simulation.

    Alternatively, you can provide an override file to use, in which case that
    one will be used rather than generating a new one.

    Warning
    -------
        It is currently not possible to provide both an override file and
        extend it!

    Example
    -------
        In your YAML, you can specify::

            pism:
                # This config file will be used as a template rather than the
                # one in model_dir!
                config_file: "/some/path/to/a/config/file"
                overrides_kv_pairs:
                    "frontal_melt.given.period": 3

        Alternatively::

            pism:
                overrides_file: "/some/path/to/an/overrides/file.nc"

    Parameters
    ----------
    config : dict
        The entire exp config

    Returns
    -------
    config : dict
        The entire exp config
    """
    if config["pism"].get("debug_override_file_generation"):
        import pdb; pdb.set_trace()
    pism_config_location = (
        config["pism"].get("config_file")
        or config["pism"]["model_dir"] + "./share/pism/pism_config.nc"
    )
    pism_overrides_location = config["pism"].get("overrides_file")
    if not pism_overrides_location:
        try:
            pism_standard_config = xr.open_dataset(pism_config_location)
        except FileNotFoundError:
            logger.error("Unable to open the default PISM config file, sorry!")
            logger.error("Was looking here:")
            logger.error(pism_config_location)
            sys.exit(1)
        new_attrs = {}
        for key, value in config["pism"].get("overrides_kv_pairs", {}).items():
            logger.debug(f"Overrides file: {key} {value}")
            if key in pism_standard_config.pism_config.attrs:
                new_attrs[key] = value
                logger.info(f"The pism_overrides.nc file will contain {key}: {value}")
            else:
                logger.error(f"Unknown PISM configuration key: {key}")
                sys.exit(1)
        pism_standard_config.pism_config.attrs = new_attrs
        logger.info("Writing a new pism_overrides.nc file!")
        new_pism_overrides = config["pism"]["thisrun_config_dir"] + "/pism_overrides.nc"
        pism_standard_config.to_netcdf(new_pism_overrides)
    else:
        logger.info(f"Using specified pism_overrides {pism_overrides_location}")
    for needed_dict in ["config_files", "config_sources", "config_in_work"]:
        if needed_dict not in config["pism"]:
            config["pism"][needed_dict] = {}
    config["pism"]["config_files"]["pism_overrides"] = "pism_overrides"
    config["pism"]["config_sources"]["pism_overrides"] = (
        pism_overrides_location or new_pism_overrides
    )
    config["pism"]["config_in_work"]["pism_overrides"] = os.path.basename(
        config["pism"]["config_sources"]["pism_overrides"]
    )
    config["pism"]["pism_command_line_opts"].append(
        "-pism_override "
        + os.path.basename(config["pism"]["config_sources"]["pism_overrides"])
    )
    return config


@logger.catch
def pism_assemble_command(config):
    """
    Puts together the final PISM command used to launch the model

    Parameters
    ----------
    config : dict
        The entire exp config

    Returns
    -------
    config : dict
        The entire exp config
    """
    command_to_run = (
        config["pism"]["executable"]
        + " -i "
        + os.path.basename(config["pism"]["input_in_work"]["input"])
        + f" -ys {config['pism']['current_year']} "
        + f" -y {config['general']['nyear']} "
        + " ".join(set(config["pism"]["pism_command_line_opts"]))
        + f" -ts_file {config['pism']['output_files']['ts_file']}"
        + f" -ts_vars "
        + ",".join(config["pism"]["ts_vars"])
        + f" -ts_times {config['pism']['ts_times']}"
        + f" -extra_file {config['pism']['output_files']['ex_file']}"
        + " -extra_vars "
        + ",".join(config["pism"]["ex_vars"])
        + f" -extra_times {config['pism']['ex_times']}"
        + f" -o {config['pism']['restart_out_in_workdir']['restart']}"
        + f" -o_size {config['pism']['output_size']} -options_left"
    )

    logger.critical("PISM will be run like this:")
    logger.critical(command_to_run)
    config["pism"]["execution_command"] = command_to_run

    return config
