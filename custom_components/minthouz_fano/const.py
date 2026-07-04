"""Constants for the Minthouz Fano P12L (IR) integration."""

from enum import IntEnum

from infrared_protocols.commands import Command
from infrared_protocols.commands.nec import NECCommand

DOMAIN = "minthouz_fano"

CONF_INFRARED_ENTITY_ID = "infrared_entity_id"

# The remote uses vanilla NEC with a fixed address byte of 0x00. Codes were
# captured with `ir-keytable -s rc0 -p nec -t` off the physical remote.
NEC_ADDRESS = 0x00

SPEED_RANGE = (1, 3)  # (min, max) integer speed levels


class FanoCode(IntEnum):
    """NEC command bytes learned from the physical Minthouz Fano P12L remote."""

    POWER = 0x57
    LED = 0x43
    TIMER_2H = 0x05
    TIMER_4H = 0x11
    TIMER_6H = 0x06
    SPEED_1 = 0x1B
    SPEED_2 = 0x12
    SPEED_3 = 0x5F

    def to_command(self, repeat_count: int = 0) -> Command:
        """Build the infrared_protocols Command for this button."""
        return NECCommand(
            address=NEC_ADDRESS, command=self.value, repeat_count=repeat_count
        )


SPEED_CODES = {
    1: FanoCode.SPEED_1,
    2: FanoCode.SPEED_2,
    3: FanoCode.SPEED_3,
}

# The LED has no dedicated per-level command — a single button cycles
# off -> low -> medium -> high -> off on every press. Brightness values
# chosen to split 0-255 evenly across the 3 "on" levels.
LED_BRIGHTNESS_LEVELS = [85, 170, 255]
