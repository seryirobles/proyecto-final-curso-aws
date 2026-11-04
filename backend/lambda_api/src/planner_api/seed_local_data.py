"""Dev-only tool: seeds local DynamoDB with 4 test accounts and a varied set
of library recipes for manual app testing (`docs/local_development.md`) — no
`feature_list.json` entry, no spec, same category as `local_server.py`. Run
via `uv run python -m planner_api.seed_local_data` from `backend/lambda_api/`."""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass

from planner_core.application.account_admin import BootstrapOutcome, bootstrap_admin, create_user
from planner_core.application.authentication import set_password
from planner_core.domain.authentication_guards import SetPasswordNotPending
from planner_core.domain.candidate import UNKNOWN_USER_ID
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.role import Role
from planner_core.domain.units import Unit
from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.clock import SystemClock
from planner_core.ports.password_hasher import Pbkdf2PasswordHasher
from planner_core.ports.recipes import LibraryRecipe

from planner_api.adapters.dynamo._table import create_data_table
from planner_api.adapters.dynamo.accounts import DynamoAccountRepository
from planner_api.adapters.dynamo.recipes import DynamoRecipeRepository

logger = logging.getLogger("planner_api.seed_local_data")

# >= password_policy.MIN_LENGTH (10); create_user itself never validates the
# password it is handed (only set_password does), but every credential here
# stays real-policy-shaped anyway so none of these accounts is a bad example.
_TEMP_PASSWORD = "TempPass1234"


@dataclass(frozen=True)
class _SeedAccount:
    user_id: str
    username: str
    role: Role
    password_reset_required: bool
    password: str  # what the account can currently log in with


_ACCOUNTS = (
    _SeedAccount("user1", "user1", Role.USER, False, "UserActive1234"),
    _SeedAccount("user2", "user2", Role.USER, True, _TEMP_PASSWORD),
    _SeedAccount("admin1", "admin1", Role.ADMIN, False, "AdminActive1234"),
    _SeedAccount("admin2", "admin2", Role.ADMIN, True, _TEMP_PASSWORD),
)


def _reseed_active(
    account: _SeedAccount,
    *,
    accounts: DynamoAccountRepository,
    hasher: Pbkdf2PasswordHasher,
) -> str:
    """A prior run can die between creation and set_password, leaving an
    "-active" account stuck on the temp password. Retry set_password here;
    SetPasswordNotPending (not UsernameAlreadyTaken) is the real "done" signal."""
    if account.password_reset_required:
        return "already seeded"
    try:
        set_password(account.user_id, account.password, accounts=accounts, hasher=hasher)
    except SetPasswordNotPending:
        pass
    return "already seeded"


def _seed_account(
    account: _SeedAccount,
    *,
    accounts: DynamoAccountRepository,
    hasher: Pbkdf2PasswordHasher,
    clock: SystemClock,
) -> str:
    try:
        if account.role is Role.USER:
            create_user(
                Role.ADMIN,
                account.user_id,
                account.username,
                hasher.hash(_TEMP_PASSWORD),
                accounts=accounts,
                clock=clock,
            )
        else:
            outcome = bootstrap_admin(
                account.user_id,
                account.username,
                hasher.hash(_TEMP_PASSWORD),
                accounts=accounts,
                clock=clock,
            )
            if outcome is BootstrapOutcome.UNCHANGED:
                return _reseed_active(account, accounts=accounts, hasher=hasher)
        # Both paths create pending (R11, G-96) — translate to the seed's target state.
        if not account.password_reset_required:
            set_password(account.user_id, account.password, accounts=accounts, hasher=hasher)
    except UsernameAlreadyTaken:
        return _reseed_active(account, accounts=accounts, hasher=hasher)

    return "created"


def _log_summary(results: list[tuple[_SeedAccount, str]]) -> None:
    logger.info("Seeded accounts:")
    for account, status in results:
        pending = "yes" if account.password_reset_required else "no"
        logger.info(
            "  username=%-20s role=%-5s reset_pending=%-3s password=%r  [%s]",
            account.username,
            account.role.value,
            pending,
            account.password,
            status,
        )


@dataclass(frozen=True)
class _SeedRecipe:
    id: str
    author: str
    name: str
    category: IngredientCategory
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    servings: int | None = None
    estimated_time: int | None = None


_G = Unit.GRAM
_ML = Unit.MILLILITRE
_U = Unit.UNIT

# Manual-testing fixtures for library/candidates/rules/shopping-list screens.
# Deliberately varied, not realistic meal-planning data: covers every
# IngredientCategory/Unit, servings/estimated_time edge values (absent, 0,
# 1, 20, near the G-90 ceiling), ingredient/tools/procedure length extremes,
# name edge cases (accents, apostrophe, ampersand, quotes, 100+ chars), a
# normalized-name collision pair, and one UNKNOWN_USER_ID-authored entry.
_RECIPES = (
    # --- MEAT ---
    _SeedRecipe(
        "pollo-al-ajillo",
        "user1",
        "Pollo al ajillo",
        IngredientCategory.MEAT,
        (
            Ingredient("pollo troceado", 800, _G),
            Ingredient("ajo", 6, _U),
            Ingredient("aceite de oliva", 50, _ML),
            Ingredient("vino blanco", 100, _ML),
        ),
        ("sartén", "cuchillo"),
        (
            "Trocear el pollo y salpimentar.",
            "Dorar el ajo laminado en aceite.",
            "Añadir el pollo y dorar por todos los lados.",
            "Verter el vino blanco y cocinar a fuego lento 15 minutos.",
        ),
        servings=4,
        estimated_time=35,
    ),
    _SeedRecipe(
        # G-90 near-ceiling estimated_time; also the big-batch (servings=20) case.
        "estofado-de-ternera-lento",
        "user2",
        "Estofado de ternera a fuego muy lento",
        IngredientCategory.MEAT,
        (
            Ingredient("ternera para estofar", 1500, _G),
            Ingredient("cebolla", 300, _G),
            Ingredient("zanahoria", 200, _G),
            Ingredient("patata", 400, _G),
            Ingredient("vino tinto", 300, _ML),
            Ingredient("caldo de carne", 500, _ML),
            Ingredient("laurel", 2, _U),
        ),
        ("olla a presión", "cuchillo", "tabla de cortar"),
        (
            "Cortar la ternera en tacos grandes.",
            "Dorar la carne en la olla con un poco de aceite.",
            "Añadir la cebolla y la zanahoria y rehogar.",
            "Incorporar la patata troceada.",
            "Verter el vino tinto y dejar reducir.",
            "Añadir el caldo de carne y el laurel.",
            "Cocinar a fuego muy lento durante horas hasta que la carne esté tierna.",
        ),
        servings=20,
        estimated_time=4200,
    ),
    _SeedRecipe(
        "alitas-de-pollo-picantes",
        "user1",
        "Alitas de pollo picantes",
        IngredientCategory.MEAT,
        (
            Ingredient("alitas de pollo", 1000, _G),
            Ingredient("salsa picante", 80, _ML),
            Ingredient("miel", 30, _G),
            Ingredient("ajo en polvo", 5, _G),
        ),
        ("horno", "bol", "papel de hornear"),
        (
            "Mezclar la salsa picante con la miel y el ajo en polvo.",
            "Bañar las alitas con la mezcla.",
            "Hornear a 200°C durante 35 minutos, dando la vuelta a mitad de cocción.",
        ),
        servings=4,
    ),
    _SeedRecipe(
        "albondigas-en-salsa",
        "user2",
        "Albóndigas en salsa",
        IngredientCategory.MEAT,
        (
            Ingredient("carne picada mixta", 500, _G),
            Ingredient("pan rallado", 50, _G),
            Ingredient("huevo", 1, _U),
            Ingredient("tomate triturado", 400, _G),
            Ingredient("cebolla", 100, _G),
        ),
        ("sartén", "bol"),
        (
            "Mezclar la carne picada con el pan rallado y el huevo.",
            "Formar las albóndigas.",
            "Freír las albóndigas hasta dorarlas.",
            "Preparar la salsa de tomate con la cebolla pochada.",
            "Cocinar las albóndigas en la salsa 15 minutos.",
        ),
        servings=4,
        estimated_time=45,
    ),
    _SeedRecipe(
        # FR-AUTH-13 reattribution placeholder: the one UNKNOWN_USER_ID author.
        "carne-mechada",
        UNKNOWN_USER_ID,
        "Carne mechada",
        IngredientCategory.MEAT,
        (
            Ingredient("falda de ternera", 1000, _G),
            Ingredient("pimiento rojo", 150, _G),
            Ingredient("cebolla", 150, _G),
            Ingredient("caldo de carne", 300, _ML),
        ),
        ("olla", "tenedor"),
        (
            "Cocinar la carne en el caldo hasta que esté muy tierna.",
            "Desmechar la carne con un tenedor.",
            "Rehogar el pimiento y la cebolla.",
            "Mezclar la carne desmechada con el sofrito.",
        ),
        servings=6,
        estimated_time=180,
    ),
    # --- FISH ---
    _SeedRecipe(
        "salmon-al-horno",
        "user1",
        "Salmón al horno con limón",
        IngredientCategory.FISH,
        (
            Ingredient("lomo de salmón", 600, _G),
            Ingredient("limón", 1, _U),
            Ingredient("aceite de oliva", 30, _ML),
            Ingredient("eneldo", 5, _G),
        ),
        ("horno", "bandeja de horno"),
        (
            "Colocar el salmón en la bandeja.",
            "Rociar con aceite y zumo de limón.",
            "Espolvorear con eneldo.",
            "Hornear a 180°C durante 18 minutos.",
        ),
        servings=2,
        estimated_time=30,
    ),
    _SeedRecipe(
        "bacalao-al-pil-pil",
        "user2",
        "Bacalao al pil-pil",
        IngredientCategory.FISH,
        (
            Ingredient("bacalao desalado", 500, _G),
            Ingredient("aceite de oliva", 200, _ML),
            Ingredient("ajo", 4, _U),
            Ingredient("guindilla", 1, _U),
        ),
        ("cazuela de barro",),
        (
            "Confitar el ajo y la guindilla en el aceite a fuego bajo.",
            "Añadir el bacalao con la piel hacia arriba.",
            "Ligar la salsa moviendo la cazuela en círculos hasta emulsionar.",
        ),
        estimated_time=40,
    ),
    _SeedRecipe(
        # Single ingredient, single tool, single step; servings=1 low edge.
        "merluza-a-la-plancha",
        "user1",
        "Merluza a la plancha",
        IngredientCategory.FISH,
        (Ingredient("lomo de merluza", 200, _G),),
        ("plancha",),
        ("Cocinar el lomo de merluza en la plancha caliente 2 minutos por cada lado.",),
        servings=1,
        estimated_time=6,
    ),
    _SeedRecipe(
        "boquerones-en-vinagre",
        "user2",
        "Boquerones en vinagre",
        IngredientCategory.FISH,
        (
            Ingredient("boquerones", 500, _G),
            Ingredient("vinagre de vino blanco", 200, _ML),
            Ingredient("ajo", 2, _U),
            Ingredient("perejil", 10, _G),
        ),
        ("bandeja", "cuchillo"),
        (
            "Limpiar y filetear los boquerones.",
            "Cubrir con vinagre y refrigerar 4 horas.",
            "Escurrir, aliñar con ajo, perejil y aceite.",
        ),
        servings=4,
    ),
    # --- CARBOHYDRATE ---
    _SeedRecipe(
        # 10+ ingredients, several tools, many procedure steps.
        "paella-de-marisco",
        "user1",
        "Paella de marisco",
        IngredientCategory.CARBOHYDRATE,
        (
            Ingredient("arroz bomba", 400, _G),
            Ingredient("caldo de pescado", 1000, _ML),
            Ingredient("gambas", 300, _G),
            Ingredient("mejillones", 300, _G),
            Ingredient("calamar", 200, _G),
            Ingredient("tomate triturado", 100, _G),
            Ingredient("pimiento rojo", 100, _G),
            Ingredient("cebolla", 100, _G),
            Ingredient("ajo", 3, _U),
            Ingredient("azafrán", 1, _G),
            Ingredient("aceite de oliva", 60, _ML),
            Ingredient("sal", 5, _G),
        ),
        ("paellera", "cuchara de madera", "cazo", "colador"),
        (
            "Sofreír la cebolla, el ajo y el pimiento en la paellera.",
            "Añadir el tomate triturado y cocinar unos minutos.",
            "Incorporar el arroz y sofreír ligeramente.",
            "Añadir el azafrán y el caldo de pescado caliente.",
            "Distribuir las gambas, los mejillones y el calamar.",
            "Cocinar a fuego medio-alto 10 minutos sin remover.",
            "Bajar el fuego y cocinar 8 minutos más.",
            "Dejar reposar 5 minutos antes de servir.",
        ),
        servings=6,
        estimated_time=50,
    ),
    _SeedRecipe(
        # Normalized-name collision pair, part 1/2 (text.normalize casefolds
        # and strips, so this matches the trailing-space entry below).
        "tortilla-de-patatas",
        "user1",
        "Tortilla de Patatas",
        IngredientCategory.CARBOHYDRATE,
        (
            Ingredient("patata", 600, _G),
            Ingredient("huevo", 6, _U),
            Ingredient("cebolla", 150, _G),
            Ingredient("aceite de oliva", 200, _ML),
        ),
        ("sartén", "bol"),
        (
            "Pelar y cortar las patatas y la cebolla.",
            "Freír a fuego lento en abundante aceite.",
            "Batir los huevos y mezclar con las patatas escurridas.",
            "Cuajar la tortilla por ambos lados en la sartén.",
        ),
        servings=4,
        estimated_time=40,
    ),
    _SeedRecipe(
        # Normalized-name collision pair, part 2/2 — different id and content.
        "tortilla-de-patatas-2",
        "user2",
        "tortilla de patatas ",
        IngredientCategory.CARBOHYDRATE,
        (
            Ingredient("patata", 500, _G),
            Ingredient("huevo", 5, _U),
            Ingredient("sal", 3, _G),
        ),
        ("sartén",),
        (
            "Freír las patatas a fuego lento.",
            "Mezclar con el huevo batido y sal.",
            "Cuajar la tortilla en la sartén.",
        ),
    ),
    _SeedRecipe(
        "noquis-de-calabaza-asados",
        "user2",
        "Ñoquis de calabaza asados",
        IngredientCategory.CARBOHYDRATE,
        (
            Ingredient("calabaza", 500, _G),
            Ingredient("harina", 200, _G),
            Ingredient("huevo", 1, _U),
            Ingredient("queso parmesano", 50, _G),
            Ingredient("mantequilla", 30, _G),
        ),
        ("horno", "bol", "tenedor"),
        (
            "Asar la calabaza hasta que esté tierna.",
            "Triturar la pulpa y mezclar con la harina y el huevo.",
            "Formar los ñoquis con un tenedor.",
            "Cocer en agua hirviendo hasta que floten.",
            "Saltear en mantequilla y espolvorear con parmesano.",
        ),
        servings=4,
        estimated_time=60,
    ),
    _SeedRecipe(
        # 100+ character name, to check the frontend doesn't truncate/choke.
        "macarrones-gratinados-atun-maiz-queso",
        "user1",
        "Receta tradicional de macarrones gratinados con tomate, atún, maíz "
        "dulce y mucho queso rallado por encima, tal y como los hacía mi abuela",
        IngredientCategory.CARBOHYDRATE,
        (
            Ingredient("macarrones", 400, _G),
            Ingredient("tomate frito", 300, _G),
            Ingredient("atún en conserva", 160, _G),
            Ingredient("maíz dulce", 100, _G),
            Ingredient("queso rallado", 150, _G),
        ),
        ("olla", "horno", "fuente para horno"),
        (
            "Cocer los macarrones según el paquete.",
            "Mezclar con el tomate frito, el atún y el maíz.",
            "Colocar en una fuente y cubrir con queso rallado.",
            "Gratinar en el horno hasta dorar.",
        ),
        servings=4,
        estimated_time=35,
    ),
    # --- LEGUME ---
    _SeedRecipe(
        "lentejas-estofadas",
        "user1",
        "Lentejas estofadas",
        IngredientCategory.LEGUME,
        (
            Ingredient("lentejas", 300, _G),
            Ingredient("zanahoria", 100, _G),
            Ingredient("patata", 150, _G),
            Ingredient("chorizo", 100, _G),
            Ingredient("caldo de verduras", 600, _ML),
        ),
        ("olla",),
        (
            "Rehogar la verdura en la olla.",
            "Añadir las lentejas, el chorizo y el caldo.",
            "Cocinar a fuego medio 40 minutos.",
        ),
        servings=4,
        estimated_time=50,
    ),
    _SeedRecipe(
        "garbanzos-con-espinacas",
        "user2",
        "Garbanzos con espinacas",
        IngredientCategory.LEGUME,
        (
            Ingredient("garbanzos cocidos", 400, _G),
            Ingredient("espinacas frescas", 200, _G),
            Ingredient("ajo", 2, _U),
            Ingredient("pimentón", 5, _G),
            Ingredient("aceite de oliva", 30, _ML),
        ),
        ("sartén",),
        (
            "Rehogar el ajo en aceite.",
            "Añadir las espinacas hasta que reduzcan.",
            "Incorporar los garbanzos y el pimentón.",
            "Cocinar 5 minutos removiendo.",
        ),
        estimated_time=20,
    ),
    _SeedRecipe(
        # 10+ ingredients, many procedure steps.
        "fabada-asturiana",
        "user1",
        "Fabada asturiana",
        IngredientCategory.LEGUME,
        (
            Ingredient("fabes", 500, _G),
            Ingredient("chorizo", 150, _G),
            Ingredient("morcilla", 150, _G),
            Ingredient("panceta", 150, _G),
            Ingredient("tocino", 100, _G),
            Ingredient("laurel", 2, _U),
            Ingredient("cebolla", 100, _G),
            Ingredient("ajo", 2, _U),
            Ingredient("azafrán", 1, _G),
            Ingredient("agua", 1500, _ML),
        ),
        ("olla", "espumadera"),
        (
            "Poner las fabes en remojo la noche anterior.",
            "Colocar las fabes en la olla junto con las carnes y el laurel.",
            "Cubrir con agua y llevar a ebullición.",
            "Desespumar y bajar el fuego.",
            "Cocinar a fuego lento durante dos horas, añadiendo agua fría de vez en cuando.",
            "Rectificar de sal y dejar reposar antes de servir.",
        ),
        servings=8,
        estimated_time=150,
    ),
    _SeedRecipe(
        # Single-step procedure.
        "hummus-rapido",
        "user2",
        "Hummus rápido",
        IngredientCategory.LEGUME,
        (
            Ingredient("garbanzos cocidos", 400, _G),
            Ingredient("tahini", 30, _G),
            Ingredient("limón", 1, _U),
            Ingredient("ajo", 1, _U),
        ),
        ("batidora",),
        ("Triturar todos los ingredientes juntos hasta obtener una crema homogénea.",),
        estimated_time=10,
    ),
    # --- VEGETABLE ---
    _SeedRecipe(
        # estimated_time=0 edge value (no-cook dish).
        "ensalada-de-tomate-rapida",
        "user1",
        "Ensalada de tomate rápida",
        IngredientCategory.VEGETABLE,
        (
            Ingredient("tomate", 300, _G),
            Ingredient("aceite de oliva", 20, _ML),
            Ingredient("sal", 2, _G),
        ),
        ("cuchillo",),
        ("Cortar el tomate en rodajas.", "Aliñar con aceite y sal."),
        servings=2,
        estimated_time=0,
    ),
    _SeedRecipe(
        "gazpacho-andaluz",
        "user2",
        "Gazpacho andaluz",
        IngredientCategory.VEGETABLE,
        (
            Ingredient("tomate", 1000, _G),
            Ingredient("pepino", 200, _G),
            Ingredient("pimiento verde", 100, _G),
            Ingredient("pan", 50, _G),
            Ingredient("aceite de oliva", 80, _ML),
            Ingredient("vinagre de jerez", 20, _ML),
        ),
        ("batidora",),
        (
            "Trocear todas las verduras.",
            "Triturar junto con el pan, el aceite y el vinagre.",
            "Colar y refrigerar antes de servir.",
        ),
        servings=6,
        estimated_time=15,
    ),
    _SeedRecipe(
        # 10+ ingredients.
        "menestra-de-verduras",
        "user1",
        "Menestra de verduras",
        IngredientCategory.VEGETABLE,
        (
            Ingredient("judía verde", 150, _G),
            Ingredient("zanahoria", 150, _G),
            Ingredient("guisantes", 100, _G),
            Ingredient("alcachofa", 150, _G),
            Ingredient("coliflor", 150, _G),
            Ingredient("espárrago", 100, _G),
            Ingredient("jamón serrano", 50, _G),
            Ingredient("ajo", 2, _U),
            Ingredient("aceite de oliva", 30, _ML),
            Ingredient("caldo de verduras", 200, _ML),
        ),
        ("olla", "sartén"),
        (
            "Cocer por separado cada verdura al punto.",
            "Saltear el jamón y el ajo en la sartén.",
            "Añadir las verduras cocidas y saltear juntas.",
            "Añadir un poco de caldo y dejar reducir.",
        ),
        servings=4,
        estimated_time=45,
    ),
    _SeedRecipe(
        # Accent/ñ name edge case.
        "champinon-relleno-jamon",
        "user2",
        "Champiñón relleno con jamón",
        IngredientCategory.VEGETABLE,
        (
            Ingredient("champiñones grandes", 500, _G),
            Ingredient("jamón serrano", 80, _G),
            Ingredient("queso rallado", 60, _G),
            Ingredient("ajo", 2, _U),
        ),
        ("horno", "bol"),
        (
            "Vaciar los champiñones y picar los tallos.",
            "Mezclar los tallos con el jamón, el ajo y el queso.",
            "Rellenar los champiñones con la mezcla.",
            "Hornear a 190°C durante 15 minutos.",
        ),
        servings=4,
    ),
    _SeedRecipe(
        # Double-quote name edge case (frontend escaping check).
        "salsa-brava-alioli",
        "user1",
        'Salsa "brava" con alioli',
        IngredientCategory.VEGETABLE,
        (
            Ingredient("tomate triturado", 400, _G),
            Ingredient("pimentón picante", 10, _G),
            Ingredient("ajo", 4, _U),
            Ingredient("aceite de oliva", 100, _ML),
            Ingredient("huevo", 1, _U),
        ),
        ("batidora", "cazo"),
        (
            "Cocinar el tomate triturado con el pimentón picante.",
            "Triturar el ajo, el huevo y el aceite hasta emulsionar para el alioli.",
            "Servir la salsa brava acompañada del alioli.",
        ),
        estimated_time=25,
    ),
    # --- EGGS ---
    _SeedRecipe(
        # Single ingredient, single tool, single step, servings=1.
        "huevo-cocido",
        "user2",
        "Huevo cocido",
        IngredientCategory.EGGS,
        (Ingredient("huevo", 2, _U),),
        ("cazo",),
        ("Cocer el huevo en agua hirviendo durante 10 minutos.",),
        servings=1,
        estimated_time=10,
    ),
    _SeedRecipe(
        "huevos-rotos-con-patatas",
        "user1",
        "Huevos rotos con patatas",
        IngredientCategory.EGGS,
        (
            Ingredient("patata", 400, _G),
            Ingredient("huevo", 4, _U),
            Ingredient("jamón serrano", 100, _G),
            Ingredient("aceite de oliva", 150, _ML),
        ),
        ("sartén", "plato para servir"),
        (
            "Freír las patatas cortadas en bastones.",
            "Freír los huevos con la yema poco cuajada.",
            "Colocar los huevos sobre las patatas y romper la yema.",
            "Añadir el jamón por encima.",
        ),
        servings=2,
        estimated_time=30,
    ),
    _SeedRecipe(
        # Ampersand name edge case.
        "huevos-bacon-americana",
        "user2",
        "Huevos & bacon a la americana",
        IngredientCategory.EGGS,
        (
            Ingredient("huevo", 3, _U),
            Ingredient("bacon", 100, _G),
            Ingredient("mantequilla", 10, _G),
        ),
        ("sartén",),
        (
            "Freír el bacon hasta que quede crujiente.",
            "Freír los huevos en la misma sartén.",
            "Servir juntos.",
        ),
        servings=1,
        estimated_time=15,
    ),
    _SeedRecipe(
        # Apostrophe name edge case.
        "crema-catalana-abuela",
        "user1",
        "Crema catalana d'la abuela",
        IngredientCategory.EGGS,
        (
            Ingredient("leche", 500, _ML),
            Ingredient("yema de huevo", 6, _U),
            Ingredient("azúcar", 100, _G),
            Ingredient("maicena", 20, _G),
            Ingredient("canela en rama", 1, _U),
            Ingredient("piel de limón", 1, _U),
        ),
        ("cazo", "soplete de cocina"),
        (
            "Infusionar la leche con la canela y la piel de limón.",
            "Batir las yemas con el azúcar y la maicena.",
            "Mezclar con la leche colada y cocinar hasta espesar.",
            "Repartir en cuencos y enfriar.",
            "Quemar el azúcar por encima con el soplete antes de servir.",
        ),
        servings=6,
        estimated_time=90,
    ),
)


def _seed_recipe(seed: _SeedRecipe, *, recipes: DynamoRecipeRepository) -> None:
    recipe = Recipe(
        name=seed.name,
        ingredients=seed.ingredients,
        tools=seed.tools,
        procedure=seed.procedure,
        category=seed.category,
        servings=seed.servings,
        estimated_time=seed.estimated_time,
    )
    recipes.save(LibraryRecipe(id=seed.id, recipe=recipe, author=seed.author))


def _log_recipe_summary(seeds: tuple[_SeedRecipe, ...]) -> None:
    logger.info("Seeded library recipes:")
    for seed in seeds:
        logger.info(
            "  id=%-40s category=%-13s author=%-13s name=%r",
            seed.id,
            seed.category.value,
            seed.author,
            seed.name,
        )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow running without DYNAMODB_ENDPOINT_URL set (same as SEED_FORCE=1).",
    )
    args = parser.parse_args(argv)

    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL")
    forced = args.force or os.environ.get("SEED_FORCE") == "1"
    if not endpoint and not forced:
        logger.error(
            "Refusing to run: DYNAMODB_ENDPOINT_URL is not set, which risks "
            "writing fake test accounts into a real AWS table. Pass --force or "
            "set SEED_FORCE=1 to seed anyway."
        )
        return 1

    accounts_to_seed: tuple[_SeedAccount, ...] = _ACCOUNTS
    if not endpoint:
        logger.warning("DYNAMODB_ENDPOINT_URL is not set — seeding against real AWS.")
        # --force covers only the 2 User accounts: a real Admin account with a
        # hardcoded, documented password is never worth the convenience.
        logger.warning("Admin seeding is local-only — skipping the 2 Admin accounts.")
        accounts_to_seed = tuple(a for a in _ACCOUNTS if a.role is not Role.ADMIN)
    else:
        logger.info("Seeding local DynamoDB at %s", endpoint)

    create_data_table()
    accounts = DynamoAccountRepository()
    hasher = Pbkdf2PasswordHasher()
    clock = SystemClock()

    results: list[tuple[_SeedAccount, str]] = []
    for account in accounts_to_seed:
        status = _seed_account(account, accounts=accounts, hasher=hasher, clock=clock)
        results.append((account, status))

    _log_summary(results)

    # save() is an upsert by id (PutItem) — always safe to re-run, unlike
    # the account loop above, so no real-vs-forced-AWS split is needed here.
    recipes = DynamoRecipeRepository()
    for seed in _RECIPES:
        _seed_recipe(seed, recipes=recipes)
    _log_recipe_summary(_RECIPES)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
