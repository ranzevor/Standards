extends SceneTree

func valid_quantity(value: Variant) -> bool:
    return typeof(value) == TYPE_INT and value >= 0

func _initialize() -> void:
    if not valid_quantity(0) or not valid_quantity(7):
        quit(1)
        return
    for invalid in [true, -1, 0.5, null]:
        if valid_quantity(invalid):
            quit(2)
            return
    var states: Dictionary = {"a": {"epoch": 2, "value": 4}, "b": {"epoch": 1, "value": 9}}
    if apply(states, "a", 1, 0):
        quit(3)
        return
    if states["a"]["value"] != 4 or not apply(states, "b", 1, 10):
        quit(4)
        return
    print("godot-contract-ok")
    quit(0)

func apply(states: Dictionary, identity: String, epoch: int, value: int) -> bool:
    if not states.has(identity) or states[identity]["epoch"] != epoch:
        return false
    states[identity]["value"] = value
    return true
