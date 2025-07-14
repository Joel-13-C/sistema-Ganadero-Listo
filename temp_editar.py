@app.route('/editar-animal/<int:animal_id>', methods=['GET', 'POST'])
def editar_animal(animal_id):
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener el animal a editar
    try:
        # No usar usuario_id para verificar permisos
        animal = db_connection.obtener_animal_por_id(animal_id)
        
        if not animal:
            flash('Animal no encontrado', 'error')
            return redirect(url_for('animales'))
        
        # Normalizar la ruta de la imagen
        if animal['foto_path']:
            # Si la ruta no comienza con 'static/', agregarla
            if not animal['foto_path'].startswith('static/'):
                animal['foto_path'] = f'static/{animal["foto_path"]}'
        else:
            # Usar imagen de marcador de posición
            animal['foto_path'] = 'static/images/upload-image-placeholder.svg'
        
        if request.method == 'POST':
            # Procesar el formulario de edición
            datos_animal = {
                'nombre': request.form.get('nombre'),
                'numero_arete': request.form.get('numero_arete'),
                'raza': request.form.get('raza'),
                'sexo': request.form.get('sexo'),
                'condicion': request.form.get('condicion'),
                'foto_path': animal['foto_path'],
                'fecha_nacimiento': request.form.get('fecha_nacimiento'),
                'propietario': request.form.get('propietario'),
                'padre_arete': request.form.get('padre_arete'),
                'madre_arete': request.form.get('madre_arete')
            }
            
            # Actualizar foto si se proporciona
            foto = request.files.get('foto')
            if foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                foto.save(filepath)
                datos_animal['foto_path'] = f'static/uploads/animales/{filename}'
            
            # Llamar al método de actualización en la base de datos
            try:
                db_connection.actualizar_animal(animal_id, datos_animal)
                # Registrar la actividad en el sistema de auditoría
                auditoria.registrar_actividad(
                    accion='Actualizar', 
                    modulo='Animales', 
                    descripcion=f'Se actualizó la información del animal ID: {animal_id}'
                )
                return jsonify({
                    'success': True,
                    'message': 'Animal actualizado exitosamente'
                })
            except Exception as e:
                app.logger.error(f'Error al actualizar el animal: {str(e)}')
                return jsonify({
                    'success': False,
                    'message': f'Error al actualizar el animal: {str(e)}'
                })
        
        return render_template('editar_animal.html', animal=animal)
    
    except Exception as e:
        app.logger.error(f'Error al editar el animal: {str(e)}')
        flash(f'Error al editar el animal: {str(e)}', 'error')
        return redirect(url_for('animales'))
