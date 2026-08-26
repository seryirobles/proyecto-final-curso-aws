"""The single backend es-ES messages module (FR-UX-03): every user-facing
string a backend package raises lives here, in UPPER_SNAKE constants — the
backend counterpart of frontend/src/messages/."""

from __future__ import annotations

PASSWORD_TOO_SHORT = "La contraseña debe tener al menos 10 caracteres."
USERNAME_ALREADY_TAKEN = "Este nombre de usuario ya está en uso."
USERNAME_RESERVED = "Este nombre de usuario está reservado y no puede utilizarse."

AI_GENERATION_INVALID_OUTPUT = "La receta generada no es válida. Puedes intentarlo de nuevo."
AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES = (
    "No hay suficientes recetas en la biblioteca para completar la semana "
    "con este modo. Añade recetas, cambia de modo o ajusta las reglas."
)
AI_GENERATION_UNAVAILABLE = (
    "La generación con IA no está disponible en este momento. Puedes intentarlo más tarde."
)
