"""
utils/forms.py
Utilitaires pour la validation et le parsing des formulaires

Factorise les conversions de types et validations répétées dans les routes.
"""
from typing import Optional, Any, List, Tuple


def parse_float(value: Any, default: float = 0.0) -> float:
    """
    Parse sécurisé d'un float depuis un formulaire.
    
    Gère les cas : None, chaîne vide, espaces, valeurs invalides.
    
    Args:
        value: Valeur à convertir (depuis request.form.get())
        default: Valeur par défaut si conversion impossible
    
    Returns:
        float: Valeur convertie ou default
    
    Examples:
        >>> parse_float('3.14')
        3.14
        >>> parse_float('')
        0.0
        >>> parse_float(None)
        0.0
        >>> parse_float('  2.5  ')
        2.5
        >>> parse_float('invalid', default=-1.0)
        -1.0
    """
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convertir en string et nettoyer
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
        int: Valeur convertie ou default
    
    Examples:
        >>> parse_int('42')
        42
        >>> parse_int('')
        0
        >>> parse_int('3.7')  # Tronque la partie décimale
        3
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
        # Gérer les floats en string (ex: '3.7' -> 3)
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
    
    Examples:
        >>> parse_int_or_none('30')
        30
        >>> parse_int_or_none('')
        None
        >>> parse_int_or_none(None)
        None
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
    
    Examples:
        >>> parse_float_or_none('50.5')
        50.5
        >>> parse_float_or_none('')
        None
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
        float: Valeur >= 0
    
    Examples:
        >>> parse_positive_float('5.5')
        5.5
        >>> parse_positive_float('-3')
        0.0
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
        int: Valeur >= 0
    """
    result = parse_int(value, default)
    return max(0, result)


def validate_required(value: Any, field_name: str) -> str:
    """
    Valide qu'un champ requis n'est pas vide.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour le message d'erreur
    
    Returns:
        str: Valeur nettoyée
    
    Raises:
        ValueError: Si la valeur est vide
    
    Examples:
        >>> validate_required('  test  ', 'nom')
        'test'
        >>> validate_required('', 'nom')
        ValueError: Le champ 'nom' est requis
    """
    if value is None:
        raise ValueError(f"Le champ '{field_name}' est requis")
    
    str_value = str(value).strip()
    
    if not str_value:
        raise ValueError(f"Le champ '{field_name}' est requis")
    
    return str_value


def validate_positive(value: float, field_name: str = "valeur") -> float:
    """
    Valide qu'une valeur numérique est strictement positive.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour le message d'erreur
    
    Returns:
        float: La valeur validée
    
    Raises:
        ValueError: Si la valeur est <= 0
    """
    if value <= 0:
        raise ValueError(f"Le champ '{field_name}' doit être positif")
    return value


def validate_non_negative(value: float, field_name: str = "valeur") -> float:
    """
    Valide qu'une valeur numérique est positive ou nulle.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour le message d'erreur
    
    Returns:
        float: La valeur validée
    
    Raises:
        ValueError: Si la valeur est < 0
    """
    if value < 0:
        raise ValueError(f"Le champ '{field_name}' ne peut pas être négatif")
    return value


def validate_range(value: float, min_val: float, max_val: float, 
                   field_name: str = "valeur") -> float:
    """
    Valide qu'une valeur est dans une plage donnée.
    
    Args:
        value: Valeur à valider
        min_val: Valeur minimale (inclusive)
        max_val: Valeur maximale (inclusive)
        field_name: Nom du champ pour le message d'erreur
    
    Returns:
        float: La valeur validée
    
    Raises:
        ValueError: Si la valeur est hors de la plage
    """
    if value < min_val or value > max_val:
        raise ValueError(
            f"Le champ '{field_name}' doit être entre {min_val} et {max_val}"
        )
    return value


def parse_checkbox(value: Any) -> bool:
    """
    Parse une valeur de checkbox HTML.
    
    Les checkboxes envoient 'on' si cochées, ou sont absentes si non cochées.
    
    Args:
        value: Valeur du formulaire (généralement 'on' ou None)
    
    Returns:
        bool: True si coché, False sinon
    
    Examples:
        >>> parse_checkbox('on')
        True
        >>> parse_checkbox(None)
        False
        >>> parse_checkbox('true')
        True
    """
    if value is None:
        return False
    
    if isinstance(value, bool):
        return value
    
    str_value = str(value).lower().strip()
    return str_value in ('on', 'true', '1', 'yes', 'oui')


def clean_string(value: Any, default: str = '') -> str:
    """
    Nettoie et retourne une chaîne de caractères.
    
    Args:
        value: Valeur à nettoyer
        default: Valeur par défaut si None ou vide
    
    Returns:
        str: Chaîne nettoyée (strip)
    
    Examples:
        >>> clean_string('  hello  ')
        'hello'
        >>> clean_string(None, 'default')
        'default'
    """
    if value is None:
        return default
    
    str_value = str(value).strip()
    return str_value if str_value else default


def clean_string_or_none(value: Any) -> Optional[str]:
    """
    Nettoie une chaîne, retourne None si vide.
    
    Utile pour les champs optionnels comme categorie.
    
    Args:
        value: Valeur à nettoyer
    
    Returns:
        str ou None
    
    Examples:
        >>> clean_string_or_none('  test  ')
        'test'
        >>> clean_string_or_none('')
        None
    """
    if value is None:
        return None
    
    str_value = str(value).strip()
    return str_value if str_value else None


# ============================================
# HELPERS SPÉCIFIQUES À L'APPLICATION
# ============================================

def parse_nutrition_values(form_data: dict) -> dict:
    """
    Parse toutes les valeurs nutritionnelles depuis un formulaire.
    
    Args:
        form_data: Dictionnaire du formulaire (request.form)
    
    Returns:
        dict: Dictionnaire des valeurs nutritionnelles
    
    Example:
        >>> values = parse_nutrition_values(request.form)
        >>> ingredient.calories = values['calories']
    """
    return {
        'calories': parse_float(form_data.get('calories')),
        'proteines': parse_float(form_data.get('proteines')),
        'glucides': parse_float(form_data.get('glucides')),
        'lipides': parse_float(form_data.get('lipides')),
        'fibres': parse_float(form_data.get('fibres')),
        'sucres': parse_float(form_data.get('sucres')),
        'sel': parse_float(form_data.get('sel')),
    }


def parse_ingredient_form(form_data: dict) -> dict:
    """
    Parse les données d'un formulaire d'ingrédient.
    
    Args:
        form_data: Dictionnaire du formulaire (request.form)
    
    Returns:
        dict: Données parsées prêtes pour créer/modifier un Ingredient
    
    Raises:
        ValueError: Si le nom est manquant
    """
    data = {
        'nom': validate_required(form_data.get('nom'), 'nom'),
        'unite': clean_string(form_data.get('unite'), 'g'),
        'prix_unitaire': parse_float(form_data.get('prix_unitaire')),
        'categorie': clean_string_or_none(form_data.get('categorie')),
        'poids_piece': parse_float_or_none(form_data.get('poids_piece')),
    }
    
    # Ajouter les valeurs nutritionnelles
    data.update(parse_nutrition_values(form_data))
    
    return data


def parse_recette_form(form_data: dict) -> dict:
    """
    Parse les données de base d'un formulaire de recette.
    
    Args:
        form_data: Dictionnaire du formulaire (request.form)
    
    Returns:
        dict: Données parsées pour créer/modifier une Recette
    
    Raises:
        ValueError: Si le nom est manquant
    """
    return {
        'nom': validate_required(form_data.get('nom'), 'nom'),
        'instructions': clean_string_or_none(form_data.get('instructions')),
        'type_recette': clean_string_or_none(form_data.get('type_recette')),
        'temps_preparation': parse_int_or_none(form_data.get('temps_preparation')),
    }


def parse_ingredients_list(form_data: dict) -> List[Tuple[int, float]]:
    """
    Parse la liste des ingrédients depuis un formulaire de recette.
    
    Attend des champs nommés ingredient_0, quantite_0, ingredient_1, quantite_1, etc.
    
    Args:
        form_data: Dictionnaire du formulaire
    
    Returns:
        list: Liste de tuples (ingredient_id, quantite)
    
    Example:
        >>> ingredients = parse_ingredients_list(request.form)
        >>> for ing_id, quantite in ingredients:
        ...     # Créer IngredientRecette
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


def parse_etapes_list(form_data: dict) -> List[str]:
    """
    Parse la liste des étapes depuis un formulaire de recette.
    
    Attend des champs nommés etape_desc_0, etape_desc_1, etc.
    
    Args:
        form_data: Dictionnaire du formulaire
    
    Returns:
        list: Liste des descriptions d'étapes (non vides)
    """
    etapes = []
    j = 0
    
    while True:
        etape_desc = form_data.get(f'etape_desc_{j}')
        
        if etape_desc is None:
            break
        
        etape_desc = etape_desc.strip()
        if etape_desc:
            etapes.append(etape_desc)
        
        j += 1
    
    return etapes
