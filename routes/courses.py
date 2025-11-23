from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, ListeCourses, StockFrigo

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        items = ListeCourses.query.filter_by(achete=False).all()
        
        for item in items:
            item_id = str(item.id)
            if request.form.get(f'achete_{item_id}'):
                quantite = float(request.form.get(f'quantite_{item_id}', item.quantite))
                
                stock = StockFrigo.query.filter_by(ingredient_id=item.ingredient_id).first()
                if stock:
                    stock.quantite += quantite
                else:
                    stock = StockFrigo(ingredient_id=item.ingredient_id, quantite=quantite)
                    db.session.add(stock)
                
                item.achete = True
        
        db.session.commit()
        flash('Frigo mis à jour avec vos achats !', 'success')
        return redirect(url_for('courses.liste'))
    
    items = ListeCourses.query.filter_by(achete=False).all()
    historique = ListeCourses.query.filter_by(achete=True).order_by(ListeCourses.id.desc()).limit(10).all()
    
    return render_template('courses.html', items=items, historique=historique)

@courses_bp.route('/retirer/<int:id>')
def retirer(id):
    item = ListeCourses.query.get_or_404(id)
    nom = item.ingredient.nom
    db.session.delete(item)
    db.session.commit()
    flash(f'{nom} retiré de la liste de courses.', 'success')
    return redirect(url_for('courses.liste'))
