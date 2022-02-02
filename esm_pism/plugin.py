import os
import sys

from loguru import logger
import xarray as xr

VALID_PISM_COUPLERS = ["ocean", "surface", "atmosphere"]

def _kv_list_to_dict_of_dicts(kv_list):
    new_dict = {}
    for item in kv_list:
        if not isinstance(item, dict):
            raise TypeError("Something in one of your kv_pairs is not correct. These should be lists or dictionaries!")
        else:
            new_dict.update(item)
    return new_dict

@logger.catch
def _add_files(coupler_files, config):
    """Adds files to a specific coupler"""

    # LA: add dual hemipshere option
    if "pism_nh" in config:
        pism_key = "pism_nh"
    elif "pism_sh" in config:
        pism_key = "pism_sh"
    else:
        pism_key = "pism"

    command_line_args = []
    for file_tag, file_path in coupler_files.items():
        command_line_args.append(f"-{file_tag} {os.path.basename(file_path)}")
        for needed_dict in ["forcing_files", "forcing_sources", "forcing_in_work"]:
            if needed_dict not in config[pism_key]:
                config[pism_key][needed_dict] = {}
        config[pism_key]["forcing_files"][file_tag] = file_tag
        config[pism_key]["forcing_sources"][file_tag] = file_path
        config[pism_key]["forcing_in_work"][file_tag] = os.path.basename(file_path)
    return command_line_args


@logger.catch
def _add_kv(coupler_key_value, config):
    """Adds kv pairs for a coupler"""
    if isinstance(coupler_key_value, list):
        coupler_key_value = _kv_list_to_dict_of_dicts(coupler_key_value)
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
    
    # LA: add dual hemipshere option
    if "pism_nh" in config:
        pism_key = "pism_nh"
    elif "pism_sh" in config:
        pism_key = "pism_sh"
    else:
        pism_key = "pism"
    
    coupler_dict = config[pism_key].get("couplers", {})
    pism_command_line_opts = config[pism_key].get("pism_command_line_opts", [])
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
    config[pism_key]["pism_command_line_opts"] = (
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

    
    # LA: add dual hemipshere option
    if "pism_nh" in config:
        pism_key = "pism_nh"
    elif "pism_sh" in config:
        pism_key = "pism_sh"
    else:
        pism_key = "pism"
    
    kv_pairs = config[pism_key].get("kv_pairs", {})
    if isinstance(kv_pairs, list):
        kv_pairs = _kv_list_to_dict_of_dicts(kv_pairs)
    pism_command_line_opts = config[pism_key].get("pism_command_line_opts", [])

    pism_command_line_opts += [
        f"{key} {value}" if key.startswith("-") else f"-{key} {value}"
        for key, value in kv_pairs.items()
    ]
    config[pism_key]["pism_command_line_opts"] = pism_command_line_opts
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
    
    # LA: add dual hemipshere option
    if "pism_nh" in config:
        pism_key = "pism_nh"
    elif "pism_sh" in config:
        pism_key = "pism_sh"
    else:
        pism_key = "pism"
    
    flags = config[pism_key].get("flags", [])
    pism_command_line_opts = config[pism_key].get("pism_command_line_opts", [])
    pism_command_line_opts += [
        f"{flag}" if flag.startswith("-") else f"-{flag}" for flag in flags
    ]
    config[pism_key]["pism_command_line_opts"] = pism_command_line_opts
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
    
    # LA: add dual hemipshere option
    if "pism_nh" in config:
        pism_key = "pism_nh"
    elif "pism_sh" in config:
        pism_key = "pism_sh"
    else:
        pism_key = "pism"
    
    if config[pism_key].get("debug_override_file_generation"):
        import pdb; pdb.set_trace()
    pism_config_location = (
        config[pism_key].get("config_file")
        or config[pism_key]["model_dir"] + "./share/pism/pism_config.nc"
    )
    pism_overrides_location = config[pism_key].get("overrides_file")
    if not pism_overrides_location:
        try:
            pism_standard_config = xr.open_dataset(pism_config_location)
        except FileNotFoundError:
            logger.error("Unable to open the default PISM config file, sorry!")
            logger.error("Was looking here:")
            logger.error(pism_config_location)
            sys.exit(1)
        new_attrs = {}
        overrides_kv_pairs = config[pism_key].get("overrides_kv_pairs", {})
        if isinstance(overrides_kv_pairs, list):
            overrides_kv_pairs = _kv_list_to_dict_of_dicts(overrides_kv_pairs)
        for key, value in overrides_kv_pairs.items():
            logger.debug(f"Overrides file: {key} {value}")
            if key in pism_standard_config.pism_config.attrs:
                new_attrs[key] = value
                logger.info(f"The pism_overrides.nc file will contain {key}: {value}")
            else:
                logger.error(f"Unknown PISM configuration key: {key}")
                sys.exit(1)
        pism_standard_config.pism_config.attrs = new_attrs
        logger.info("Writing a new pism_overrides.nc file!")
        new_pism_overrides = config[pism_key]["thisrun_config_dir"] + "/pism_overrides.nc"
        pism_standard_config.to_netcdf(new_pism_overrides)
    else:
        logger.info(f"Using specified pism_overrides {pism_overrides_location}")
    for needed_dict in ["config_files", "config_sources", "config_in_work"]:
        if needed_dict not in config[pism_key]:
            config[pism_key][needed_dict] = {}
    config[pism_key]["config_files"]["pism_overrides"] = "pism_overrides"
    config[pism_key]["config_sources"]["pism_overrides"] = (
        pism_overrides_location or new_pism_overrides
    )
    config[pism_key]["config_in_work"]["pism_overrides"] = os.path.basename(
        config[pism_key]["config_sources"]["pism_overrides"]
    )
    config[pism_key]["pism_command_line_opts"].append(
        "-pism_override "
        + os.path.basename(config[pism_key]["config_sources"]["pism_overrides"])
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
    
    # LA: add dual hemipshere option
    if "pism_nh" in config:
        pism_key = "pism_nh"
    elif "pism_sh" in config:
        pism_key = "pism_sh"
    else:
        pism_key = "pism"

    command_to_run = (
        config[pism_key]["executable"]
        + " -i "
        + os.path.basename(config[pism_key]["input_targets"]["input"])
        + " -ys " + str(config[pism_key]['current_year'])
        + " -y " + str(config['general']['nyear']) + " "
        + " ".join(set(config[pism_key]["pism_command_line_opts"])) + " "
        + " -ts_file " + str(config[pism_key]['outdata_sources']['ts_file']) + " "
        + " -ts_vars "
        + ",".join(config[pism_key]["ts_vars"]) + " "
        + " -ts_times " + str(config[pism_key]['ts_times']) + " "
        + " -extra_file " + str(config[pism_key]['outdata_sources']['ex_file']) + " "
        + " -extra_vars "
        + ",".join(config[pism_key]["ex_vars"]) + " "
        + " -extra_times " + str(config[pism_key]['ex_times']) + " "
        + " -o " + str(config[pism_key]['restart_out_sources']['restart']) + " "
        + " -o_size " + str(config[pism_key]['outdata_size']) + " -options_left"
    )

    logger.critical("PISM will be run like this:")
    logger.critical(command_to_run)
    config[pism_key]["execution_command"] = command_to_run

    return config
