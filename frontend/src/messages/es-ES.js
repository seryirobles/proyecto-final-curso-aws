/**
 * Every user-facing string lives here (docs/conventions.md section "Castilian
 * Spanish"; FR-UX-01, FR-UX-03). No component, hook or handler holds a
 * Spanish string literal — it imports a key from this module instead.
 */

export const MESSAGES = {
  APP_TITLE: 'Planificador semanal',
  SCAFFOLD_PLACEHOLDER_TITLE: 'Planificador semanal',
  SCAFFOLD_PLACEHOLDER_BODY: 'La aplicación todavía no tiene pantallas de producto.',

  // Shared infrastructure (feature 20 T1-T13)
  GENERIC_ERROR: 'Se ha producido un error inesperado. Inténtalo de nuevo más tarde.',
  CONFIRM_DIALOG_CONFIRM: 'Confirmar',
  CONFIRM_DIALOG_CANCEL: 'Cancelar',
  LOADING_STATE_DEFAULT: 'Cargando…',
  WEEK_LABEL_CURRENT: 'Semana actual',
  WEEK_LABEL_NEXT: 'Semana próxima',

  // Week planner (feature 20 T14-T17)
  WEEK_PLANNER_EMPTY_SLOT: 'Todavía no hay platos para este hueco.',
  WEEK_PLANNER_ADD_CANDIDATE: 'Añadir plato',
  WEEK_PLANNER_PROMOTE_DEFINITIVE: 'Marcar como definitivo',
  WEEK_PLANNER_CLEAR_DEFINITIVE: 'Quitar definitivo',
  WEEK_PLANNER_DEFINITIVE_BADGE: 'Definitivo',
  CONFIRM_REPLACE_DEFINITIVE: '¿Reemplazar el plato definitivo de este hueco?',
  CONFIRM_CLEAR_DEFINITIVE: '¿Quitar el plato definitivo de este hueco?',
  // Candidate edit/remove (issue add-dish-button-inert scope extension)
  WEEK_PLANNER_EDIT_CANDIDATE: 'Editar',
  WEEK_PLANNER_REMOVE_CANDIDATE: 'Eliminar',
  CONFIRM_REMOVE_CANDIDATE: '¿Eliminar este plato de este hueco?',
  // Day-card status pill (feature 20 T81, design.md 10.6)
  WEEK_PLANNER_DAY_STATUS_EMPTY: 'Sin platos',
  WEEK_PLANNER_DAY_STATUS_CANDIDATES: 'Con candidatas',
  WEEK_PLANNER_DAY_STATUS_DEFINITIVE: 'Definitiva lista',

  // Recipe detail (feature 20 T18-T21)
  RECIPE_DETAIL_CLOSE: 'Cerrar',
  RECIPE_DETAIL_SERVINGS: 'Comensales',
  RECIPE_DETAIL_ESTIMATED_TIME: 'Tiempo estimado (minutos)',
  RECIPE_DETAIL_INGREDIENTS: 'Ingredientes',
  RECIPE_DETAIL_TOOLS: 'Utensilios',
  RECIPE_DETAIL_PROCEDURE: 'Elaboración',

  // Shared authoring flow (feature 20 T22-T24)
  RECIPE_AUTHORING_METHOD_LIBRARY: 'Elegir de la biblioteca',
  RECIPE_AUTHORING_METHOD_SCRATCH: 'Escribir desde cero',
  RECIPE_AUTHORING_METHOD_AI: 'Generar con IA',
  RECIPE_AUTHORING_NAME_LABEL: 'Nombre',
  RECIPE_AUTHORING_CATEGORY_LABEL: 'Categoría',
  RECIPE_AUTHORING_CATEGORY_PLACEHOLDER: 'Selecciona una categoría',
  RECIPE_AUTHORING_SERVINGS_LABEL: 'Comensales',
  RECIPE_AUTHORING_ESTIMATED_TIME_LABEL: 'Tiempo estimado (minutos)',
  RECIPE_AUTHORING_INGREDIENTS_LABEL: 'Ingredientes',
  RECIPE_AUTHORING_INGREDIENT_NAME_LABEL: 'Nombre del ingrediente',
  RECIPE_AUTHORING_INGREDIENT_QUANTITY_LABEL: 'Cantidad',
  // Issue negative-ingredient-quantity, E5/E11: non-blank, non-positive value.
  RECIPE_AUTHORING_INVALID_QUANTITY: 'La cantidad del ingrediente debe ser mayor que cero.',
  RECIPE_AUTHORING_INVALID_SERVINGS: 'El número de comensales debe ser mayor que cero.',
  // Issue recipe-saved-without-required-sections, E8: wording mirrors
  // planner_core.messages' RECIPE_WITHOUT_* (backend/core/src/planner_core/messages.py).
  RECIPE_AUTHORING_MISSING_INGREDIENTS: 'La receta debe incluir al menos un ingrediente.',
  RECIPE_AUTHORING_MISSING_TOOLS: 'La receta debe incluir al menos un utensilio.',
  RECIPE_AUTHORING_MISSING_PROCEDURE: 'La receta debe incluir al menos un paso de elaboración.',
  RECIPE_AUTHORING_UNIT_PLACEHOLDER: 'Selecciona una unidad',
  RECIPE_AUTHORING_ADD_INGREDIENT: 'Añadir ingrediente',
  RECIPE_AUTHORING_REMOVE_INGREDIENT: 'Quitar ingrediente',
  RECIPE_AUTHORING_TOOLS_LABEL: 'Utensilios',
  RECIPE_AUTHORING_ADD_TOOL: 'Añadir utensilio',
  RECIPE_AUTHORING_REMOVE_TOOL: 'Quitar utensilio',
  RECIPE_AUTHORING_PROCEDURE_LABEL: 'Elaboración',
  RECIPE_AUTHORING_ADD_STEP: 'Añadir paso',
  RECIPE_AUTHORING_REMOVE_STEP: 'Quitar paso',
  RECIPE_AUTHORING_SUBMIT: 'Guardar receta',
  RECIPE_AUTHORING_REFERENCE_RECIPE_LABEL: 'Receta de referencia',
  RECIPE_AUTHORING_NOTES_LABEL: 'Notas',
  // Single-recipe AI generation (feature 28)
  AI_LIST_HINT: 'Separa cada elemento con una coma o un salto de línea.',
  AI_GENERATE: 'Generar receta',
  AI_GENERATING: 'Generando la receta…',
  AI_PREVIEW_TITLE: 'Receta generada',
  AI_ACCEPT: 'Aceptar receta',
  AI_DISCARD: 'Descartar',
  AI_REGENERATE: 'Volver a generar',

  // Library recipe picker + library view (feature 20 T25-T31)
  LIBRARY_PICKER_NAME_LABEL: 'Buscar por nombre',
  LIBRARY_PICKER_CATEGORY_LABEL: 'Categoría',
  LIBRARY_PICKER_CATEGORY_ALL: 'Todas las categorías',
  LIBRARY_PICKER_SELECT: 'Seleccionar',
  LIBRARY_PICKER_SELECTED: 'Seleccionada',
  LIBRARY_PICKER_EMPTY: 'No se han encontrado recetas con estos filtros.',
  LIBRARY_VIEW_TITLE: 'Biblioteca de recetas',
  LIBRARY_VIEW_ADD: 'Añadir receta',
  LIBRARY_VIEW_EDIT: 'Editar',
  LIBRARY_VIEW_REMOVE: 'Eliminar',
  LIBRARY_VIEW_EMPTY: 'Todavía no hay recetas en la biblioteca.',
  CONFIRM_REMOVE_LIBRARY_RECIPE: '¿Eliminar esta receta de la biblioteca?',

  // Rules view (feature 20 T32-T34)
  RULES_VIEW_TITLE: 'Reglas de generación',
  RULES_VIEW_EMPTY: 'Todavía no hay reglas configuradas.',
  RULES_CATEGORY_COUNT_SECTION_TITLE: 'Cantidad por categoría',
  RULES_CATEGORY_LABEL: 'Categoría',
  RULES_CATEGORY_PLACEHOLDER: 'Selecciona una categoría',
  RULES_COUNT_LABEL: 'Cantidad',
  RULES_COUNT_PLACEHOLDER: 'Selecciona una cantidad',
  RULES_PIN_SECTION_TITLE: 'Platos fijados',
  RULES_DAY_LABEL: 'Día',
  RULES_DAY_PLACEHOLDER: 'Selecciona un día',
  RULES_SLOT_LABEL: 'Comida',
  RULES_SLOT_PLACEHOLDER: 'Selecciona una comida',
  RULES_DISABLED_DAY_SECTION_TITLE: 'Días desactivados',
  RULES_SAVE: 'Guardar regla',
  RULES_REMOVE: 'Eliminar',
  RULES_CONFLICT_PREFIX: 'Entra en conflicto con:',
  CONFIRM_REMOVE_RULE: '¿Eliminar esta regla?',

  // Shopping list view (feature 20 T35-T37)
  SHOPPING_LIST_VIEW_TITLE: 'Lista de la compra',
  SHOPPING_LIST_VIEW_EMPTY: 'Todavía no hay elementos en la lista de la compra.',
  SHOPPING_LIST_UNCHECKED_SECTION_TITLE: 'Por comprar',
  SHOPPING_LIST_CHECKED_SECTION_TITLE: 'Comprado',
  SHOPPING_LIST_ADD: 'Añadir elemento',
  SHOPPING_LIST_EDIT: 'Editar',
  SHOPPING_LIST_REMOVE: 'Eliminar',
  SHOPPING_LIST_NAME_LABEL: 'Nombre',
  SHOPPING_LIST_QUANTITY_LABEL: 'Cantidad',
  SHOPPING_LIST_UNIT_LABEL: 'Unidad',
  SHOPPING_LIST_UNIT_PLACEHOLDER: 'Selecciona una unidad',
  SHOPPING_LIST_SAVE_ADD: 'Añadir',
  SHOPPING_LIST_SAVE_EDIT: 'Guardar cambios',
  SHOPPING_LIST_CANCEL: 'Cancelar',
  SHOPPING_LIST_RESYNC: 'Resincronizar',
  SHOPPING_LIST_RESYNC_SCOPE_LABEL:
    'Se resincronizará desde hoy hasta el final de la semana próxima:',
  SHOPPING_LIST_RESYNC_SCOPE_CONNECTOR: 'y',
  SHOPPING_LIST_RESYNC_IN_PROGRESS: 'Resincronizando…',
  CONFIRM_REMOVE_SHOPPING_ITEM: '¿Eliminar este elemento de la lista de la compra?',

  // Summary view (feature 20 T38-T40)
  SUMMARY_VIEW_TITLE: 'Resumen de la semana',
  SUMMARY_VIEW_EMPTY: 'Todavía no hay platos definitivos para esta semana.',

  // App shell (feature 20 T41-T45)
  NAV_WEEK: 'Semana',
  NAV_LIBRARY: 'Biblioteca',
  NAV_RULES: 'Reglas',
  NAV_SHOPPING_LIST: 'Lista de la compra',
  NAV_SUMMARY: 'Resumen',
  CONNECTION_LOST: 'Se ha perdido la conexión. Reconectando…',

  // Auth screens - login, set-password (feature 20 T46-T53)
  LOGIN_VIEW_TITLE: 'Iniciar sesión',
  LOGIN_USERNAME_LABEL: 'Usuario',
  LOGIN_PASSWORD_LABEL: 'Contraseña',
  LOGIN_SUBMIT: 'Entrar',
  // Auth screens - card styling reopen (feature 20 T79-T80, design.md 10.6)
  LOGIN_NO_REGISTRATION_NOTE: 'Sin registro público. Las cuentas las crea el administrador.',
  SET_PASSWORD_VIEW_TITLE: 'Nueva contraseña',
  SET_PASSWORD_NEW_LABEL: 'Nueva contraseña',
  SET_PASSWORD_CONFIRM_LABEL: 'Confirmar contraseña',
  SET_PASSWORD_MISMATCH: 'Las contraseñas no coinciden.',
  SET_PASSWORD_SUBMIT: 'Guardar y entrar',
  SET_PASSWORD_CANCEL: 'Cancelar',

  // Auth screens - admin accounts + app-shell logout (feature 20 T54-T60)
  APP_LOGOUT: 'Salir',
  ADMIN_ACCOUNTS_VIEW_TITLE: 'Administración de usuarios',
  ADMIN_ACCOUNTS_VIEW_EMPTY: 'Todavía no hay cuentas de usuario.',
  ADMIN_ACCOUNTS_NEW_USERNAME_LABEL: 'Nuevo usuario',
  ADMIN_ACCOUNTS_TEMP_PASSWORD_LABEL: 'Contraseña inicial',
  ADMIN_ACCOUNTS_CREATE: 'Crear',
  ADMIN_ACCOUNTS_RENAME: 'Renombrar',
  ADMIN_ACCOUNTS_RESET_PASSWORD: 'Restablecer contraseña',
  ADMIN_ACCOUNTS_REMOVE: 'Eliminar',
  ADMIN_ACCOUNTS_CANCEL: 'Cancelar',
  ADMIN_ACCOUNTS_PENDING_BADGE: 'contraseña pendiente',
  ADMIN_ACCOUNTS_CONFIRM_RESET: '¿Restablecer la contraseña de esta cuenta?',
  ADMIN_ACCOUNTS_CONFIRM_REMOVE: '¿Eliminar esta cuenta de usuario?',
};
