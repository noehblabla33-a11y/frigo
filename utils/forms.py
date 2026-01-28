"""
utils/forms.py
Utilitaires pour la validation et le parsing des formulaires

Factorise les conversions de types et validations répétées dans les routes.
"""
from typing import Optional, Any, List, Tuple, Generator


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
        >>> parse_float_or_none('3.14')
        3.14
        >>> parse_float_or_none('')
        None
        >>> parse_float_or_none(None)
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


def parse_checkbox(value: Any) -> bool:
    """
    Parse une valeur de checkbox depuis un formulaire.
    
    Args:
        value: Valeur du formulaire
    
    Returns:
        bool: True si coché, False sinon
    
    Examples:
        >>> parse_checkbox('on')
        True
        >>> parse_checkbox('1')
        True
        >>> parse_checkbox(None)
        False
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
    
    Examples:
        >>> clean_string('  hello  ')
        'hello'
        >>> clean_string(None, 'default')
        'default'
        >>> clean_string('')
        ''
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
    
    Examples:
        >>> clean_string_or_none('  hello  ')
        'hello'
        >>> clean_string_or_none('')
        None
        >>> clean_string_or_none('   ')
        None
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
    
    Raises:
        ValueError: Si la valeur est vide
    """
    cleaned = clean_string(value)
    if not cleaned:
        raise ValueError(f"Le champ '{field_name}' est requis")
    return cleaned


def parse_nutrition_values(form_data: dict) -> dict:
    """
    Parse les valeurs nutritionnelles depuis un formulaire.
    
    Attend des champs nommés: calories, proteines, glucides, lipides, fibres
    
    Args:
        form_data: Dictionnaire du formulaire (request.form)
    
    Returns:
        dict avec les clés nutritionnelles, valeurs None si non renseignées
    
    Example:
        >>> nutrition = parse_nutrition_values(request.form)
        >>> # {'calories': 250.0, 'proteines': None, ...}
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
        dict: Données parsées pour créer/modifier une Recette
    
    Raises:
        ValueError: Si le nom est manquant
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


def parse_etapes_list(form_data: dict, max_index: int = 100) -> Generator[Tuple[str, Optional[int]], None, None]:
    """
    Parse la liste des étapes depuis un formulaire de recette.
    
    Attend des champs nommés etape_desc_0, etape_duree_0, etape_desc_1, etape_duree_1, etc.
    
    VERSION ROBUSTE : Parcourt jusqu'à max_index pour trouver toutes les étapes,
    même si certains indices sont manquants (cas de suppression d'étapes).
    
    Args:
        form_data: Dictionnaire du formulaire
        max_index: Index maximum à vérifier (défaut 100)
    
    Yields:
        tuple: (description, duree_minutes) pour chaque étape non vide
               duree_minutes est None si non spécifié
    
    Example:
        >>> for description, duree in parse_etapes_list(request.form):
        ...     etape = EtapeRecette(description=description, duree_minutes=duree)
    """
    # Parcourir tous les indices possibles pour trouver les étapes
    # (permet de gérer le cas où des étapes ont été supprimées au milieu)
    for i in range(max_index):
        desc_key = f'etape_desc_{i}'
        duree_key = f'etape_duree_{i}'
        
        description = form_data.get(desc_key, '').strip()
        
        if description:
            # Récupérer aussi la durée
            duree_str = form_data.get(duree_key, '').strip()
            duree_minutes = int(duree_str) if duree_str and duree_str.isdigit() else None
            yield (description, duree_minutes)
