# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.registers.register import Register


def test_bits_are_appended_properly_and_can_be_edited_in_place():
    register = Register(name="apa", index=0, mode="r")

    bit_hest = register.append_bit(name="hest", description="abc")
    assert bit_hest.index == 0

    bit_zebra = register.append_bit(name="zebra", description="def")
    assert bit_zebra.index == 1

    bit_hest.description = "new desc"
    assert register.bits[0].description == "new desc"


def test_repr_basic():
    # Check that repr is an actual representation, not just "X object at 0xABCDEF"
    assert "apa" in repr(Register(name="apa", index=0, mode="r"))

    # Different name
    assert repr(Register(name="apa", index=0, mode="r")) != repr(
        Register(name="hest", index=0, mode="r")
    )

    # Different index
    assert repr(Register(name="apa", index=0, mode="r")) != repr(
        Register(name="apa", index=1, mode="r")
    )

    # Different mode
    assert repr(Register(name="apa", index=0, mode="r")) != repr(
        Register(name="apa", index=0, mode="w")
    )

    # Different default value
    assert repr(Register(name="apa", index=0, mode="r", default_value=3)) != repr(
        Register(name="apa", index=0, mode="r", default_value=4)
    )

    # Different description
    assert repr(Register(name="apa", index=0, mode="r", description="Blaah")) != repr(
        Register(name="apa", index=0, mode="r", description="Gaah")
    )


def test_repr_with_bits_appended():
    register_a = Register(name="apa", index=0, mode="r")
    register_a.append_bit(name="hest", description="")

    register_b = Register(name="apa", index=0, mode="r")
    register_b.append_bit(name="hest", description="")

    assert repr(register_a) == repr(register_b)

    register_a.append_bit(name="zebra", description="")
    register_b.append_bit(name="foo", description="")

    assert repr(register_a) != repr(register_b)
