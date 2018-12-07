library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library osvvm;
use osvvm.RandomPkg.all;

library vunit_lib;
use vunit_lib.memory_pkg.all;
use vunit_lib.memory_utils_pkg.all;
use vunit_lib.random_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library bfm;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_operations_pkg.all;

use work.ddr_buffer_regs_pkg.all;


entity tb_ddr_buffer is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_ddr_buffer is

  signal clk_axi : std_logic := '0';
  signal axi_read_m2s : axi_read_m2s_t := axi_read_m2s_init;
  signal axi_read_s2m : axi_read_s2m_t := axi_read_s2m_init;

  signal axi_write_m2s : axi_write_m2s_t := axi_write_m2s_init;
  signal axi_write_s2m : axi_write_s2m_t := axi_write_s2m_init;

  signal regs_m2s : axil_m2s_t := axil_m2s_init;
  signal regs_s2m : axil_s2m_t := axil_s2m_init;

  constant axi_width : integer := 64;
  constant burst_length : integer := 16;
  constant burst_size_bytes : integer := burst_length * axi_width / 8;

  constant memory : memory_t := new_memory;
  constant regs_master : bus_master_t := new_bus(data_length => 32, address_length => regs_m2s.read.ar.addr'length);
  constant axi_slave : axi_slave_t := new_axi_slave(address_fifo_depth => 1, memory => memory);

begin

  test_runner_watchdog(runner, 1 ms);
  clk_axi <= not clk_axi after 10 ns;


  ------------------------------------------------------------------------------
  main : process
    variable rnd : RandomPType;
    variable memory_data : integer_array_t := null_integer_array;
    variable buf : buffer_t;
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    random_integer_array(rnd, memory_data, width=>burst_size_bytes, bits_per_word=>8);

    buf := write_integer_array(memory, memory_data, "read data", permissions=>read_only);
    write_reg(net, regs_master, ddr_buffer_read_addr, base_address(buf));

    buf := set_expected_integer_array(memory, memory_data, "write data", permissions=>write_only);
    write_reg(net, regs_master, ddr_buffer_write_addr, base_address(buf));

    write_command(net, regs_master, ddr_buffer_command_start);
    wait_for_status_bit(net, regs_master, ddr_buffer_status_idle);

    check_expected_was_written(memory);
    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  axil_master_inst : entity bfm.axil_master
    generic map (
      bus_handle => regs_master
    )
    port map (
      clk => clk_axi,

      axil_m2s => regs_m2s,
      axil_s2m => regs_s2m
    );


  ------------------------------------------------------------------------------
  axi_slave_inst : entity bfm.axi_slave
    generic map (
      axi_slave => axi_slave,
      data_width => axi_width
    )
    port map (
      clk => clk_axi,

      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m,

      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m
    );


  ------------------------------------------------------------------------------
  dut : entity work.ddr_buffer_top
    generic map (
      axi_width => axi_width,
      burst_length => burst_length
    )
    port map (
      clk_axi_read => clk_axi,
      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m,

      clk_axi_write => clk_axi,
      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m,

      clk_regs => clk_axi,
      regs_m2s => regs_m2s,
      regs_s2m => regs_s2m
    );

end architecture;
