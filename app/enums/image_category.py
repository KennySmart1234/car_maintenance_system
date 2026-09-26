from enum import Enum


class ImageCategory(Enum):
    BEFORE = "BEFORE"
    DAMAGE_PART = "DAMAGED_PART"
    REMOVED_PART = "REMOVED_PART"
    REPLACEMENT_PART = "REPLACEMENT_PART"
    AFTER = "AFTER"
