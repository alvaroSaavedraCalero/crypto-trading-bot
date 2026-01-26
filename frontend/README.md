# Crypto Trading Dashboard - Frontend

Dashboard interactivo para monitorear estrategias de trading.

## Instalación

```bash
# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev

# Build para producción
npm run build
```

## Acceso

- **Desarrollo**: http://localhost:3000
- **API Backend**: http://localhost:8000 (configurado en proxy)

## Estructura

```
frontend/
├── src/
│   ├── components/      # Componentes reutilizables
│   │   ├── Layout.jsx
│   │   └── Sidebar.jsx
│   ├── pages/           # Páginas principales
│   │   ├── Dashboard.jsx
│   │   ├── Strategies.jsx
│   │   ├── Backtests.jsx
│   │   └── PaperTrading.jsx
│   ├── services/        # Cliente API
│   │   └── api.js
│   ├── App.jsx          # Componente raíz
│   └── main.jsx         # Punto de entrada
├── package.json
├── vite.config.js       # Configuración Vite
└── index.html           # HTML base
```

## Páginas

### Dashboard
- Vista general del sistema
- Estadísticas principales
- Estado de conexión con la API

### Estrategias
- Listar todas las estrategias creadas
- Crear nuevas estrategias
- Ver detalles, editar y eliminar

### Backtests
- Visualizar resultados de backtests
- Comparar rendimiento de estrategias
- Descargar reportes

### Paper Trading
- Monitorear sesiones activas
- Ver trades en tiempo real
- Gráficos de desempeño

## Características

- ✅ Interfaz moderna y responsiva
- ✅ Barra lateral colapsable
- ✅ Temas de colores profesionales
- ✅ Integración con API REST
- ✅ Manejo de errores
- ✅ Loading states

## Desarrollo

```bash
# Hot reload automático
npm run dev

# Build optimizado
npm run build

# Preview del build
npm run preview
```

## Variables de entorno

Crear `.env`:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Tecnologías

- **React 18** - UI
- **Vite** - Build tool
- **Axios** - HTTP client
- **React Router** - Navigation
- **Chart.js** - Gráficos
- **Tailwind CSS** - Estilos
