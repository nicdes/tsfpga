library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library common;
use common.addr_pkg.all;

library ddr_buffer;
library reg_file;
library resync;

use work.artyz7_top_pkg.all;
use work.artyz7_regs_pkg.all;


entity artyz7_top is
  port (
    clk_ext : in std_logic;
    led : out std_logic_vector(0 to 3)
  );
end entity;

architecture a of artyz7_top is

  signal clk_m_gp0 : std_logic := '0';
  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal clk_s_hp0 : std_logic := '0';
  signal s_hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal s_hp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axil_m2s_vec_t(reg_slaves'range) := (others => axil_m2s_init);
  signal regs_s2m : axil_s2m_vec_t(reg_slaves'range) := (others => axil_s2m_init);

begin

  ------------------------------------------------------------------------------
  blink_0 : process
    variable count : unsigned(27 - 1 downto 0) := (others => '0');
  begin
    wait until rising_edge(clk_m_gp0);
    led(0) <= count(count'high);
    count := count + 1;
  end process;

  blink_1 : process
    variable count : unsigned(27 - 1 downto 0) := (others => '0');
  begin
    wait until rising_edge(clk_s_hp0);
    led(1) <= count(count'high);
    count := count + 1;
  end process;


  ------------------------------------------------------------------------------
  regs_block : block
    -- Set up some registers to be in same clock domain as AXI port,
    -- and some to be in another clock domain.
    constant clocks_are_the_same : boolean_vector(reg_slaves'range) :=
      (ddr_buffer_regs_idx => false, dummy_reg_slaves => true);
  begin

    ------------------------------------------------------------------------------
    axi_to_regs_inst : entity axi.axi_to_axil_vec
      generic map (
        axil_slaves => reg_slaves,
        clocks_are_the_same => clocks_are_the_same
      )
      port map (
        clk_axi => clk_m_gp0,
        axi_m2s => m_gp0_m2s,
        axi_s2m => m_gp0_s2m,

        clk_axil_vec(ddr_buffer_regs_idx) => clk_s_hp0,
        clk_axil_vec(dummy_reg_slaves) => (dummy_reg_slaves => '0'),
        axil_vec_m2s => regs_m2s,
        axil_vec_s2m => regs_s2m
      );


    ------------------------------------------------------------------------------
    register_maps : for slave in dummy_reg_slaves generate
      axil_reg_file_inst : entity reg_file.axil_reg_file
        generic map (
          regs => artyz7_reg_map
        )
        port map (
          clk => clk_m_gp0,

          axil_m2s => regs_m2s(slave),
          axil_s2m => regs_s2m(slave)
        );
    end generate;
  end block;


  ------------------------------------------------------------------------------
  ddr_buffer_inst : entity ddr_buffer.ddr_buffer_top
    generic map (
      axi_width => s_hp0_data_width,
      burst_length => 16 -- AXI3 max
    )
    port map (
      clk_axi_read => clk_s_hp0,
      axi_read_m2s => s_hp0_m2s.read,
      axi_read_s2m => s_hp0_s2m.read,

      clk_axi_write => clk_s_hp0,
      axi_write_m2s => s_hp0_m2s.write,
      axi_write_s2m => s_hp0_s2m.write,

      clk_regs => clk_s_hp0,
      regs_m2s => regs_m2s(ddr_buffer_regs_idx),
      regs_s2m => regs_s2m(ddr_buffer_regs_idx)
    );


  ------------------------------------------------------------------------------
  block_design : block
    signal pl_clk0, pl_clk1 : std_logic := '0';
  begin

    clk_m_gp0 <= pl_clk0;
    clk_s_hp0 <= pl_clk1;

    block_design_inst : entity work.block_design_wrapper
    port map (
      clk_m_gp0 => clk_m_gp0,
      m_gp0_m2s => m_gp0_m2s,
      m_gp0_s2m => m_gp0_s2m,

      clk_s_hp0 => clk_s_hp0,
      s_hp0_m2s => s_hp0_m2s,
      s_hp0_s2m => s_hp0_s2m,

      pl_clk0 => pl_clk0,
      pl_clk1 => pl_clk1
    );
  end block;

end architecture;
