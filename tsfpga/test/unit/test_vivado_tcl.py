# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from collections import OrderedDict
from pathlib import Path
import unittest

from tsfpga.build_step_tcl_hook import BuildStepTclHook
from tsfpga.module import get_modules
from tsfpga.system_utils import create_file, delete
from tsfpga.vivado_tcl import VivadoTcl
from tsfpga.vivado_utils import to_tcl_path
from tsfpga.test.test_utils import file_contains_string


THIS_DIR = Path(__file__).parent


class TestVivadoTcl(unittest.TestCase):  # pylint: disable=too-many-instance-attributes

    modules_folder = THIS_DIR / "modules"

    def setUp(self):
        delete(self.modules_folder)

        # A library with some synth files and some test files
        self.a_vhd = to_tcl_path(create_file(self.modules_folder / "apa" / "a.vhd"))
        self.tb_a_vhd = to_tcl_path(create_file(self.modules_folder / "apa" / "test" / "tb_a.vhd"))
        self.a_xdc = to_tcl_path(create_file(self.modules_folder / "apa" / "scoped_constraints" / "a.xdc"))

        self.b_v = to_tcl_path(create_file(self.modules_folder / "apa" / "b.v"))
        self.b_tcl = to_tcl_path(create_file(self.modules_folder / "apa" / "scoped_constraints" / "b.tcl"))

        self.c_tcl = to_tcl_path(create_file(self.modules_folder / "apa" / "ip_cores" / "c.tcl"))

        # A library with only test files
        self.c_vhd = to_tcl_path(create_file(self.modules_folder / "zebra" / "test" / "c.vhd"))

        self.modules = get_modules([self.modules_folder])

        self.tcl = VivadoTcl(name="name")

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="",
            top=""
        )
        assert self.a_vhd in tcl and self.b_v in tcl
        assert self.tb_a_vhd not in tcl and "tb_a.vhd" not in tcl

    def test_different_hdl_file_types(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="",
            top=""
        )
        assert f"read_vhdl -library apa -vhdl2008 {{{self.a_vhd}}}" in tcl
        assert f"read_verilog {{{self.b_v}}}" in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="",
            top=""
        )
        assert "zebra" not in tcl

    def test_static_generics(self):
        # Use OrderedDict here in test so that order will be preserved and we can test for equality.
        # In real world case a normal dict can be used.
        generics = OrderedDict(enable=True, disable=False, integer=123, slv="4'b0101")

        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            generics=generics
        )
        expected = "\nset_property generic {enable=1'b1 disable=1'b0 integer=123 slv=4'b0101} [current_fileset]\n"
        assert expected in tcl

    def test_constraints(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top=""
        )

        expected = "\nread_xdc -ref a %s\n" % self.a_xdc
        assert expected in tcl
        expected = "\nread_xdc -ref b -unmanaged %s\n" % self.b_tcl
        assert expected in tcl

    def test_multiple_tcl_sources(self):
        extra_tcl_sources = [Path("dummy.tcl"), Path("files.tcl")]
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            tcl_sources=extra_tcl_sources
        )

        for filename in extra_tcl_sources:
            assert f"\nsource -notrace {to_tcl_path(filename)}\n" in tcl

    def test_build_step_hooks(self):
        dummy = BuildStepTclHook(Path("dummy.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
        files = BuildStepTclHook(Path("files.tcl"), "STEPS.ROUTE_DESIGN.TCL.PRE")
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            build_step_hooks=[dummy, files]
        )

        assert f"\nset_property STEPS.SYNTH_DESIGN.TCL.PRE {to_tcl_path(dummy.tcl_file)} ${{run}}\n" in tcl
        assert f"\nset_property STEPS.ROUTE_DESIGN.TCL.PRE {to_tcl_path(files.tcl_file)} ${{run}}\n" in tcl

    def test_build_step_hooks_with_same_hook_step(self):
        dummy = BuildStepTclHook(Path("dummy.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
        files = BuildStepTclHook(Path("files.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
        tcl = self.tcl.create(
            project_folder=THIS_DIR / "dummy_project_folder",
            modules=self.modules,
            part="part",
            top="",
            build_step_hooks=[dummy, files]
        )

        hook_file = THIS_DIR / "dummy_project_folder" / "hook_STEPS_SYNTH_DESIGN_TCL_PRE.tcl"

        assert file_contains_string(str(hook_file), f"source {to_tcl_path(dummy.tcl_file)}")
        assert file_contains_string(str(hook_file), f"source {to_tcl_path(files.tcl_file)}")

        assert f"\nset_property STEPS.SYNTH_DESIGN.TCL.PRE {to_tcl_path(hook_file)} ${{run}}\n" in tcl

    def test_ip_core_files(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top=""
        )
        assert "\nsource -notrace %s\n" % self.c_tcl in tcl

    def test_ip_cache_location(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
        )
        assert "config_ip_cache" not in tcl

        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            ip_cache_path=THIS_DIR
        )
        assert f"\nconfig_ip_cache -use_cache_location {to_tcl_path(THIS_DIR)}\n" in tcl

    def test_set_multiple_threads(self):
        num_threads = 2
        tcl = self.tcl.build(
            project_file=Path(),
            output_path=Path(),
            num_threads=num_threads,
            run_index=1
        )
        assert "set_param general.maxThreads %d" % num_threads in tcl
        assert "launch_runs synth_1 -jobs %d" % num_threads in tcl
        assert "launch_runs impl_1 -jobs %d" % num_threads in tcl

    def test_set_run_index(self):
        tcl = self.tcl.build(
            project_file=Path(),
            output_path=Path(),
            num_threads=0,
            run_index=1
        )
        assert "impl_1" in tcl
        assert "synth_1" in tcl
        assert "impl_2" not in tcl
        assert "synth_2" not in tcl

        tcl = self.tcl.build(
            project_file=Path(),
            output_path=Path(),
            num_threads=0,
            run_index=2
        )
        assert "impl_2" in tcl
        assert "synth_2" in tcl
        assert "impl_1" not in tcl
        assert "synth_1" not in tcl

    def test_runtime_generics(self):
        generics = dict(dummy=True)
        tcl = self.tcl.build(
            project_file=Path(),
            output_path=Path(),
            num_threads=0,
            run_index=0,
            generics=generics
        )
        expected = "\nset_property generic {dummy=1'b1} [current_fileset]\n"
        assert expected in tcl
