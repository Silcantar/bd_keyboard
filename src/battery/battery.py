from dataclasses import dataclass

from build123d import *

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

@dataclass
class BatteryParameters:
    color: ColorLike = "Silver"
    fillet_radius: float = 1
    size: vector[3] = (34, 50, 4)

class Battery(Part):
    """Standard lithium-polymer battery."""
    def __init__(
        self,
        parameters: BatteryParameters = BatteryParameters(),
        label: str = None,
        **kwargs
    ):
        self.parameters = parameters
        p = self.parameters
        if label is None:
            label = f"LiPo Battery {10*p.size[Z]}{p.size[X]}{p.size[Y]}"
        try:
            color
        except NameError:
            color = self.parameters.color
        battery = Box(*self.parameters.size)
        battery = fillet(
            objects=battery.edges().filter_by(Axis.Y),
            radius=p.fillet_radius
            )
        super().__init__(
            obj=battery,
            label=label,
            color=color,
            **kwargs
            )
        RigidJoint(
            label="face",
            to_part=self,
            joint_location=Pos(battery.faces().filter_by(-Axis.Z)[0].center())
            )


if __name__ == "__main__":
    from ocp_vscode import show
    show(Battery(), render_joints=True)