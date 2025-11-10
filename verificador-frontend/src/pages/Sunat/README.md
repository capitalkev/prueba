# Estructura del Frontend

Este documento describe la organización del código del frontend.

## Estructura de Carpetas

```
src/
├── components/          # Componentes reutilizables de React
│   ├── MetricCard.jsx
│   ├── MultiClientSelector.jsx
│   └── MultiCurrencySelector.jsx
├── constants/           # Constantes y configuración
│   └── index.js
├── icons/               # Iconos SVG como componentes React
│   └── index.jsx
├── utils/               # Funciones utilitarias
│   └── formatters.js
├── App.jsx              # Componente principal de la aplicación
├── main.jsx             # Punto de entrada de la aplicación
└── index.css            # Estilos globales

## Descripción de Carpetas

### `/components`
Contiene todos los componentes reutilizables de React:
- **MetricCard**: Tarjeta para mostrar métricas con título, valor y subvalor
- **MultiClientSelector**: Selector desplegable con múltiples opciones de clientes
- **MultiCurrencySelector**: Selector desplegable para filtrar por moneda (PEN/USD)

### `/constants`
Define las constantes utilizadas en toda la aplicación:
- `API_BASE_URL`: URL base del backend API
- `INVOICE_STATUSES`: Estados posibles de las facturas
- `CURRENCIES`: Monedas disponibles (PEN, USD)
- `STATUS_COLORS`: Mapeo de estados a clases de Tailwind CSS

### `/icons`
Iconos SVG exportados como componentes React:
- `BuildingOfficeIcon`: Icono de edificio (para clientes)
- `CurrencyDollarIcon`: Icono de moneda
- `ChevronDownIcon`: Flecha hacia abajo
- `ChevronUpIcon`: Flecha hacia arriba
- `ArrowsUpDownIcon`: Flechas de ordenamiento

### `/utils`
Funciones utilitarias reutilizables:
- **formatters.js**:
  - `formatCurrency()`: Formatea números como moneda (PEN o USD)
  - `formatPeriodDisplay()`: Convierte periodo YYYYMM a texto legible

## Componente Principal (App.jsx)

El componente `App` es el componente principal que:
1. Maneja el estado de la aplicación (ventas, paginación, filtros)
2. Realiza llamadas a la API del backend
3. Renderiza el dashboard con métricas y tabla de facturas
4. Gestiona los filtros de cliente y moneda

## Importaciones

Ejemplo de cómo importar desde cada carpeta:

```javascript
// Componentes
import MultiClientSelector from './components/MultiClientSelector';

// Iconos
import { ChevronDownIcon } from './icons';

// Constantes
import { API_BASE_URL, STATUS_COLORS } from './constants';

// Utilidades
import { formatCurrency } from './utils/formatters';
```

## Convenciones

- **Componentes**: PascalCase, un componente por archivo
- **Constantes**: UPPER_SNAKE_CASE
- **Funciones utilitarias**: camelCase
- **Archivos**: PascalCase para componentes, camelCase para utilidades
