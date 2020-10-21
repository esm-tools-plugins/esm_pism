#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `esm_pism` package."""


import os
import unittest

from esm_pism import plugin

# Test requirement:
from loguru import logger
import yaml

logger.remove()


class TestEsm_pism(unittest.TestCase):
    """Tests for `esm_pism` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        with open(
            os.path.join(os.path.dirname(__file__), "esm_pism_example.yaml"), "r"
        ) as f:
            self.example_config = yaml.safe_load(f.read())

    def test_pism_set_couplers(self):
        plugin.pism_set_couplers(self.example_config)
        command_arg_should_have = [
            "-atmosphere_given_file bar",
            "-kill_icebergs",
            "-atmosphere given,lapse_rate",
            "-ocean pik",
            "-atmosphere_given_period 1",
            "-ocean_kill_file calvemask_Greenland.240m.nc",
        ]
        for command_arg in command_arg_should_have:
            self.assertIn(
                command_arg,
                " ".join(self.example_config["pism"]["pism_command_line_opts"]),
            )

    def test_pism_set_couplers_bad_name(self):
        self.example_config["pism"]["couplers"]["lala"] = "bad thing"
        self.assertRaises(SystemExit, plugin.pism_set_couplers, self.example_config)
