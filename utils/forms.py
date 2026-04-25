from typing import Optional, Any, List, Tuple, Generator
from flask import flash
from models.models import Ingredient, Recette


def parse_float(value: Any, default: float = 0.0) -> float:
    """
    Parse sécurisé d'un float depuis un formulaire.

    Gère les cas : None, chaîne vide, espaces, valeurs invalides.

    Args:
        value: Valeur à convertir (depuis request.form.get())
        default: Valeur par défaut si conversion impossible

    Returns:
        Valeur convertie ou default
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    str_value = str(value).strip()

    if not str_value:
        return default

    try:
        return float(str_value)
    except (ValueError, TypeError):
        return default


def parse_int(value: Any, default: int = 0) -> int:
    """
    Parse sécurisé d'un int depuis un formulaire.

    Args:
        value: Valeur à convertir
        default: Valeur par défaut si conversion impossible

    Returns:
        Valeur convertie ou default
    """
    if value is None:
        return default

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    str_value = str(value).strip()

    if not str_value:
        return default

    try:
        return int(float(str_value))
    except (ValueError, TypeError):
        return default


def parse_int_or_none(value: Any) -> Optional[int]:
    """
    Parse un int, retourne None si vide ou invalide.

    Utile pour les champs optionnels comme temps_preparation.

    Args:
        value: Valeur à convertir

    Returns:
        int ou None
    """
    if value is None:
        return None

    str_value = str(value).strip()

    if not str_value:
        return None

    try:
        return int(float(str_value))
    except (ValueError, TypeError):
        return None


def parse_float_or_none(value: Any) -> Optional[float]:
    """
    Parse un float, retourne None si vide ou invalide.

    Utile pour les champs optionnels comme poids_piece.

    Args:
        value: Valeur à convertir

    Returns:
        float ou None
    """
    if value is None:
        return None

    str_value = str(value).strip()

    if not str_value:
        return None

    try:
        return float(str_value)
    except (ValueError, TypeError):
        return None


def parse_positive_float(value: Any, default: float = 0.0) -> float:
    """
    Parse un float et s'assure qu'il est positif ou nul.

    Args:
        value: Valeur à convertir
        default: Valeur par défaut

    Returns:
        Valeur >= 0
    """
    result = parse_float(value, default)
    return max(0.0, result)


def parse_positive_int(value: Any, default: int = 0) -> int:
    """
    Parse un int et s'assure qu'il est positif ou nul.

    Args:
        value: Valeur à convertir
        default: Valeur par défaut

    Returns:
        Valeur >= 0
    """
    result = parse_int(value, default)
    return max(0, result)


def parse_checkbox(value: Any) -> bool:
    """
    Parse une valeur de checkbox depuis un formulaire.

    Args:
        value: Valeur du formulaire

    Returns:
        True si coché, False sinon
    """
    if value is None:
        return False

    str_value = str(value).lower().strip()
    return str_value in ('on', '1', 'true', 'yes', 'oui')


def clean_string(value: Any, default: str = '') -> str:
    """
    Nettoie une chaîne depuis un formulaire.

    Args:
        value: Valeur à nettoyer
        default: Valeur par défaut si None/vide

    Returns:
        Chaîne nettoyée (stripped)
    """
    if value is None:
        return default

    return str(value).strip() or default


def clean_string_or_none(value: Any) -> Optional[str]:
    """
    Nettoie une chaîne, retourne None si vide.

    Utile pour les champs optionnels comme instructions.

    Args:
        value: Valeur à nettoyer

    Returns:
        Chaîne nettoyée ou None
    """
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned if cleaned else None


def validate_required(value: Any, field_name: str) -> str:
    """
    Valide qu'un champ requis n'est pas vide.

    Args:
        value: Valeur à valider
        field_name: Nom du champ (pour le message d'erreur)

    Returns:
        Valeur nettoyée
    """
    cleaned = clean_string(value)
    if not cleaned:
        raise ValueError(f"Le champ '{field_name}' est requis")
    return cleaned


def parse_nutrition_values(form_data: dict) -> dict:
    """
    Parse les valeurs nutritionnelles depuis un formulaire.

    Args:
        form_data: Dictionnaire du formulaire (request.form)

    Returns:
        Dict avec les clés nutritionnelles, valeurs None si non renseignées
    """
    fields = ['calories', 'proteines', 'glucides', 'lipides', 'fibres']
    return {
        field: parse_float_or_none(form_data.get(field))
        for field in fields
    }


def parse_recette_form(form_data: dict) -> dict:
    """
    Parse les données de base d'une recette depuis un formulaire.

    Args:
        form_data: Dictionnaire du formulaire (request.form)

    Returns:
        Données parsées pour créer/modifier une Recette
    """
    return {
        'nom': validate_required(form_data.get('nom'), 'nom'),
        'instructions': clean_string_or_none(form_data.get('instructions')),
        'type_recette': clean_string_or_none(form_data.get('type_recette')),
        'temps_preparation': parse_int_or_none(form_data.get('temps_preparation')),
        'temps_cuisson': parse_int_or_none(form_data.get('temps_cuisson'))
    }


def parse_ingredients_list(form_data: dict) -> List[Tuple[int, float]]:
    """
    Parse la liste des ingrédients depuis un formulaire de recette.

    Attend des champs nommés ingredient_0, quantite_0, ingredient_1, quantite_1, etc.

    Args:
        form_data: Dictionnaire du formulaire

    Returns:
        Liste de tuples (ingredient_id, quantite)
    """
    ingredients = []
    i = 0

    while True:
        ing_id = form_data.get(f'ingredient_{i}')

        if not ing_id:
            break

        try:
            ing_id = int(ing_id)
            quantite = parse_float(form_data.get(f'quantite_{i}'))

            if ing_id and quantite > 0:
                ingredients.append((ing_id, quantite))
        except (ValueError, TypeError):
            pass

        i += 1

    return ingredients


def parse_etapes_list(form_data: dict, max_index: int = 100) -> Generator[Tuple[str, Optional[int]], None, None]:
    """
    Parse la liste des étapes depuis un formulaire de recette.

    Attend des champs nommés etape_desc_0, etape_duree_0, etc.
    Parcourt jusqu'à max_index pour gérer les indices manquants.

    Args:
        form_data: Dictionnaire du formulaire
        max_index: Index maximum à vérifier (défaut 100)

    Yields:
        Tuple (description, duree_minutes) pour chaque étape non vide
    """
    for i in range(max_index):
        desc_key = f'etape_desc_{i}'
        duree_key = f'etape_duree_{i}'

        description = form_data.get(desc_key, '').strip()

        if description:
            duree_str = form_data.get(duree_key, '').strip()
            duree_minutes = int(duree_str) if duree_str and duree_str.isdigit() else None
            yield (description, duree_minutes)

def validate_unique_ingredient(nom: str, exclude_id: Optional[int] = None) -> bool:
    """
    Vérifie qu'un ingrédient n'existe pas déjà avec ce nom.

    Args:
        nom: Nom de l'ingrédient à vérifier
        exclude_id: ID à exclure (pour modification)

    Returns:
        True si valide (n'existe pas), False sinon
    """
    query = Ingredient.query.filter_by(nom=nom)

    if exclude_id:
        query = query.filter(Ingredient.id != exclude_id)

    if query.first():
        flash(f'L\'ingrédient "{nom}" existe déjà !', 'danger')
        return False

    return True


def validate_unique_recette(nom: str, exclude_id: Optional[int] = None) -> bool:
    """
    Vérifie qu'une recette n'existe pas déjà avec ce nom.

    Args:
        nom: Nom de la recette à vérifier
        exclude_id: ID à exclure (pour modification)

    Returns:
        True si valide, False sinon
    """
    query = Recette.query.filter_by(nom=nom)

    if exclude_id:
        query = query.filter(Recette.id != exclude_id)

    if query.first():
        flash(f'La recette "{nom}" existe déjà !', 'danger')
        return False

    return True


def validate_ingredient_not_used(ingredient: Ingredient) -> Tuple[bool, List[str]]:
    """
    Vérifie qu'un ingrédient n'est pas utilisé dans des recettes.

    Args:
        ingredient: L'ingrédient à vérifier

    Returns:
        Tuple (peut_supprimer: bool, noms_recettes: list)
    """
    recettes_utilisees = []

    for ing_rec in ingredient.recettes:
        recette = ing_rec.recette
        if recette:
            recettes_utilisees.append(recette.nom)

    if recettes_utilisees:
        if len(recettes_utilisees) <= 3:
            recettes_str = ', '.join(recettes_utilisees)
        else:
            recettes_str = ', '.join(recettes_utilisees[:3]) + f' et {len(recettes_utilisees) - 3} autre(s)'

        flash(
            f'Impossible de supprimer "{ingredient.nom}" : '
            f'utilisé dans {len(recettes_utilisees)} recette(s) ({recettes_str})',
            'danger'
        )
        return False, recettes_utilisees

    return True, []


def validate_recette_not_planned(recette: Recette) -> Tuple[bool, int]:
    """
    Vérifie qu'une recette n'a pas de planifications en cours.

    Cette fonction informe mais ne bloque pas la suppression.
    Les planifications seront supprimées en cascade.

    Args:
        recette: La recette à vérifier

    Returns:
        Tuple (peut_supprimer: bool, nb_planifications: int)
    """
    nb_planifications = len([p for p in recette.planifications if not p.preparee])

    if nb_planifications > 0:
        flash(
            f'Attention : "{recette.nom}" a {nb_planifications} planification(s) en cours. '
            f'Elles seront également supprimées.',
            'warning'
        )

    return True, nb_planifications


def validate_quantite_positive(quantite: float, nom_champ: str = 'quantité') -> bool:
    """
    Vérifie qu'une quantité est positive.

    Args:
        quantite: Valeur à vérifier
        nom_champ: Nom du champ pour le message d'erreur

    Returns:
        True si valide
    """
    if quantite is None or quantite < 0:
        flash(f'La {nom_champ} doit être un nombre positif.', 'danger')
        return False

    return True


def validate_quantite_stock_suffisant(
    ingredient_id: int,
    quantite_requise: float,
    nom_ingredient: str = None
) -> bool:
    """
    Vérifie qu'il y a assez de stock pour une opération.

    Args:
        ingredient_id: ID de l'ingrédient
        quantite_requise: Quantité nécessaire
        nom_ingredient: Nom pour le message (optionnel)

    Returns:
        True si stock suffisant
    """
    from models.models import StockFrigo

    stock = StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()
    quantite_dispo = stock.quantite if stock else 0

    if quantite_dispo < quantite_requise:
        nom = nom_ingredient or f'l\'ingrédient (ID: {ingredient_id})'
        flash(
            f'Stock insuffisant pour {nom} : '
            f'{quantite_dispo} disponible(s), {quantite_requise} requis(es).',
            'warning'
        )
        return False

    return True


def validate_categorie(categorie: str, categories_valides: List[Tuple]) -> bool:
    """
    Vérifie qu'une catégorie est valide.

    Args:
        categorie: Catégorie à vérifier
        categories_valides: Liste de tuples (nom, icone) depuis constants.py

    Returns:
        True si valide
    """
    if not categorie:
        return True

    noms_valides = [cat[0] for cat in categories_valides]

    if categorie not in noms_valides:
        flash(f'Catégorie invalide : "{categorie}"', 'danger')
        return False

    return True


def validate_type_recette(type_recette: str, types_valides: List[str]) -> bool:
    """
    Vérifie qu'un type de recette est valide.

    Args:
        type_recette: Type à vérifier
        types_valides: Liste des types depuis constants.py

    Returns:
        True si valide
    """
    if not type_recette:
        return True

    if type_recette not in types_valides:
        flash(f'Type de recette invalide : "{type_recette}"', 'danger')
        return False

    return True


def validate_image_file(file, max_size_mb: float = 5) -> bool:
    """
    Vérifie qu'un fichier uploadé est une image valide.

    Args:
        file: FileStorage de Flask
        max_size_mb: Taille maximale en MB

    Returns:
        True si valide
    """
    if not file or not file.filename:
        return True

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

    if ext not in allowed_extensions:
        flash(
            f'Format de fichier non supporté : .{ext}. '
            f'Formats acceptés : {", ".join(allowed_extensions)}',
            'danger'
        )
        return False

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > max_size_mb * 1024 * 1024:
        flash(f'Fichier trop volumineux. Maximum : {max_size_mb} MB', 'danger')
        return False

    return True


def validate_ingredient_form(
    nom: str,
    categorie: str = None,
    categories_valides: List[Tuple] = None,
    exclude_id: Optional[int] = None
) -> bool:
    """
    Valide un formulaire d'ingrédient complet.

    Args:
        nom: Nom de l'ingrédient
        categorie: Catégorie (optionnel)
        categories_valides: Liste des catégories valides
        exclude_id: ID à exclure pour la modification

    Returns:
        True si tout est valide
    """
    if not nom or not nom.strip():
        flash('Le nom de l\'ingrédient est requis.', 'danger')
        return False

    if not validate_unique_ingredient(nom, exclude_id):
        return False

    if categorie and categories_valides:
        if not validate_categorie(categorie, categories_valides):
            return False

    return True


def validate_recette_form(
    nom: str,
    type_recette: str = None,
    types_valides: List[str] = None,
    exclude_id: Optional[int] = None
) -> bool:
    """
    Valide un formulaire de recette complet.

    Args:
        nom: Nom de la recette
        type_recette: Type (optionnel)
        types_valides: Liste des types valides
        exclude_id: ID à exclure pour la modification

    Returns:
        True si tout est valide
    """
    if not nom or not nom.strip():
        flash('Le nom de la recette est requis.', 'danger')
        return False

    if not validate_unique_recette(nom, exclude_id):
        return False

    if type_recette and types_valides:
        if not validate_type_recette(type_recette, types_valides):
            return False

    return True
