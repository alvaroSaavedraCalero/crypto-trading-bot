# Guía para Limpieza de Ramas

## Situación Actual

Debido a restricciones del sistema Claude Code, las ramas deben tener el prefijo `claude/` y el sufijo del session ID para poder hacer push. Por esto, algunas operaciones deben completarse manualmente en GitHub.

## Estado Actual de Ramas

### Locales ✅
- `claude/develop-WD8Zh` - Rama principal con todo el trabajo (LISTA)

### Remotas
- ✅ `origin/main` - Rama principal
- ✅ `origin/claude/develop-WD8Zh` - Rama de desarrollo con todo el trabajo
- ⚠️ `origin/claude/code-review-feedback-uk436` - Sesión antigua (ELIMINAR)
- ⚠️ `origin/claude/refactor-complex-mkcyke3vk04g1vhb-zuuS8` - Sesión antigua (ELIMINAR)

## Pasos para Completar la Limpieza Manualmente

### Opción 1: Usando GitHub Web Interface (Recomendado)

1. **Ir a GitHub:**
   ```
   https://github.com/alvaroSaavedraCalero/crypto-trading-bot
   ```

2. **Crear rama develop desde claude/develop-WD8Zh:**
   - Ir a la página principal del repositorio
   - Hacer clic en el botón de ramas (donde dice "main")
   - En la lista de ramas, buscar `claude/develop-WD8Zh`
   - Hacer clic en los tres puntos al lado de `claude/develop-WD8Zh`
   - Seleccionar "Rename branch"
   - Cambiar nombre a `develop`

   **Alternativa:**
   - Ir a "Settings" → "Branches"
   - O crear nueva rama `develop` desde `claude/develop-WD8Zh`:
     - Click en dropdown de ramas
     - Escribir "develop"
     - Click en "Create branch: develop from claude/develop-WD8Zh"

3. **Eliminar ramas antiguas:**
   - En la página de ramas: `https://github.com/alvaroSaavedraCalero/crypto-trading-bot/branches`
   - Buscar estas ramas:
     - `claude/code-review-feedback-uk436`
     - `claude/refactor-complex-mkcyke3vk04g1vhb-zuuS8`
     - `claude/develop-WD8Zh` (solo después de crear `develop`)
   - Hacer clic en el ícono de basura 🗑️ al lado de cada rama
   - Confirmar eliminación

### Opción 2: Usando Git Localmente (Después de la Sesión)

Después de que termine esta sesión de Claude Code, puedes ejecutar:

```bash
# 1. Fetch todas las ramas
git fetch --all

# 2. Checkout a main
git checkout main
git pull origin main

# 3. Crear rama develop desde claude/develop-WD8Zh
git checkout -b develop origin/claude/develop-WD8Zh
git push -u origin develop

# 4. Eliminar ramas antiguas remotas
git push origin --delete claude/code-review-feedback-uk436
git push origin --delete claude/refactor-complex-mkcyke3vk04g1vhb-zuuS8
git push origin --delete claude/develop-WD8Zh

# 5. Limpiar referencias locales
git fetch --prune
git branch -D claude/develop-WD8Zh
```

### Opción 3: Usando GitHub CLI

Si tienes `gh` instalado:

```bash
# Renombrar rama
gh api repos/alvaroSaavedraCalero/crypto-trading-bot/branches/claude/develop-WD8Zh/rename \
  -X POST -f new_name=develop

# Eliminar ramas antiguas
gh api repos/alvaroSaavedraCalero/crypto-trading-bot/git/refs/heads/claude/code-review-feedback-uk436 \
  -X DELETE

gh api repos/alvaroSaavedraCalero/crypto-trading-bot/git/refs/heads/claude/refactor-complex-mkcyke3vk04g1vhb-zuuS8 \
  -X DELETE
```

## Resultado Final Esperado

Después de completar estos pasos, deberías tener:

### Ramas en GitHub
- ✅ `main` - Rama principal de producción
- ✅ `develop` - Rama de desarrollo con todo el trabajo optimizado

### Estado del Código
Ambas ramas tendrán todo el trabajo realizado:
- ✅ Tests corregidos (115/115 pasando)
- ✅ Estrategias optimizadas (KELTNER, BOLLINGER_MR)
- ✅ Scripts de optimización y testing
- ✅ Documentación completa
- ✅ Configuraciones actualizadas en `config/settings.py`

## Verificación

Para verificar que todo está correcto:

```bash
# Ver ramas remotas
git ls-remote --heads origin

# Deberías ver solo:
# refs/heads/main
# refs/heads/develop
```

## Contenido de las Ramas

### main
```
6bb3ebc Merge pull request #4 from alvaroSaavedraCalero/claude/develop-WD8Zh
8b73cf2 fix: Corregir parámetro n_jobs en optimizador
f7d7236 feat: Comprehensive strategy analysis framework
```

### develop (será igual a claude/develop-WD8Zh)
```
945f9d8 feat: Comprehensive strategy optimization results
8b73cf2 fix: Corregir parámetro n_jobs en optimizador
f7d7236 feat: Comprehensive strategy analysis framework
7dfb274 Merge pull request #3
c85dca8 fix: Corregir tests fallidos
```

## Notas Importantes

1. **No elimines `claude/develop-WD8Zh`** hasta que hayas creado `develop` y verificado que tiene todo el código.

2. **Verifica que `develop` tenga el commit `945f9d8`** (resultados de optimización). Este commit tiene las configuraciones optimizadas finales.

3. **La rama `main` actual puede estar desactualizada.** Considera hacer un merge de `develop` a `main` después de verificar:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

4. **Configuración de rama por defecto:** Considera establecer `develop` como rama por defecto en GitHub:
   - Settings → Branches → Default branch → Cambiar a `develop`

## Archivos Importantes en develop

- `config/settings.py` - Configuraciones optimizadas
- `OPTIMIZATION_RESULTS.md` - Resultados detallados
- `STRATEGY_ANALYSIS.md` - Análisis completo
- `optimize_best_strategies.py` - Script de optimización
- `quick_strategy_test.py` - Script de testing rápido

Todo el trabajo de optimización está documentado y listo para usar.
