# ============================================================
# AI COMMUNICATION ASSISTANT
# COMMAND ENGINE
# ============================================================

COMMANDS = {
    "hello": {
        "command": "GREETING",
        "message": "Hello! How can I help you?"
    },

    "goodbye": {
        "command": "GOODBYE",
        "message": "Goodbye!"
    },

    "thank_you": {
        "command": "THANK_YOU",
        "message": "You're welcome!"
    },

    "sorry": {
        "command": "SORRY",
        "message": "It's okay."
    },

    "please": {
        "command": "PLEASE",
        "message": "Please."
    },

    "yes": {
        "command": "YES",
        "message": "Yes."
    },

    "no": {
        "command": "NO",
        "message": "No."
    },

    "okay": {
        "command": "OKAY",
        "message": "Okay."
    },

    "help": {
        "command": "HELP",
        "message": "Help command activated."
    },

    "stop": {
        "command": "STOP",
        "message": "Stop command activated."
    },

    "come": {
        "command": "COME",
        "message": "Come."
    },

    "go": {
        "command": "GO",
        "message": "Go."
    },

    "sit": {
        "command": "SIT",
        "message": "Sit."
    },

    "stand": {
        "command": "STAND",
        "message": "Stand."
    },

    "eat": {
        "command": "EAT",
        "message": "I want to eat."
    },

    "drink": {
        "command": "DRINK",
        "message": "I want to drink."
    },

    "write": {
        "command": "WRITE",
        "message": "Write."
    },

    "read": {
        "command": "READ",
        "message": "Read."
    },

    "today": {
        "command": "TODAY",
        "message": "Today."
    },

    "where": {
        "command": "WHERE",
        "message": "Where?"
    },

    "what": {
        "command": "WHAT",
        "message": "What?"
    },

    "when": {
        "command": "WHEN",
        "message": "When?"
    },

    "me": {
        "command": "ME",
        "message": "Me."
    },

    "you": {
        "command": "YOU",
        "message": "You."
    },

    "he": {
        "command": "HE",
        "message": "He."
    },

    "she": {
        "command": "SHE",
        "message": "She."
    },

    "mother": {
        "command": "MOTHER",
        "message": "Mother."
    },

    "father": {
        "command": "FATHER",
        "message": "Father."
    },

    "brother": {
        "command": "BROTHER",
        "message": "Brother."
    },

    "sister": {
        "command": "SISTER",
        "message": "Sister."
    },

    "friend": {
        "command": "FRIEND",
        "message": "Friend."
    },

    "teacher": {
        "command": "TEACHER",
        "message": "Teacher."
    },

    "student": {
        "command": "STUDENT",
        "message": "Student."
    },

    "home": {
        "command": "HOME",
        "message": "Home."
    },

    "school": {
        "command": "SCHOOL",
        "message": "School."
    },

    "hospital": {
        "command": "HOSPITAL",
        "message": "Hospital."
    },

    "market": {
        "command": "MARKET",
        "message": "Market."
    },

    "water": {
        "command": "WATER",
        "message": "Water."
    },

    "food": {
        "command": "FOOD",
        "message": "Food."
    },

    "tea": {
        "command": "TEA",
        "message": "Tea."
    }
}


def normalize_sign(sign):
    """
    Convert incoming sign into a clean standard format.
    """

    if sign is None:
        return ""

    sign = str(sign).strip().lower()

    return sign


def execute_command(sign):
    """
    Convert a detected ISL sign into a communication command.
    """

    sign = normalize_sign(sign)

    if not sign:
        return {
            "success": False,
            "sign": "",
            "command": "UNKNOWN",
            "message": "No sign received."
        }

    if sign in COMMANDS:

        command_data = COMMANDS[sign]

        return {
            "success": True,
            "sign": sign,
            "command": command_data["command"],
            "message": command_data["message"]
        }

    return {
        "success": False,
        "sign": sign,
        "command": "UNKNOWN",
        "message": f"I don't have a command for '{sign}' yet."
    }


def get_all_commands():
    """
    Return all available commands.
    """

    return {
        "total": len(COMMANDS),
        "commands": COMMANDS
    }