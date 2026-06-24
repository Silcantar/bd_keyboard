# from dataclasses import dataclass

from build123d import *

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

class Battery(Part):
    """Standard lithium-polymer battery. Default size is 403450."""
    def __init__(
        self,
        size: vector[3] = (34, 50, 4),
        fillet_radius: float = 1,
        color: ColorLike = "Silver",
        label: str = None,
        **kwargs
    ):
        if label is None:
            label = f"LiPo Battery {10*size[Z]}{size[X]}{size[Y]}"
        battery = Box(*size)
        battery = fillet(
            objects=battery.edges().filter_by(Axis.Y),
            radius=fillet_radius
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