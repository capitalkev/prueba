import { useState, useEffect, useMemo } from "react";
import { API_BASE_URL } from "../constants";
import { signOut } from "firebase/auth";
import { auth } from "../../../firebase";

/**
 * Hook personalizado para manejar la lógica de datos de SUNAT
 * Incluye fetch de clientes, ventas paginadas y métricas
 */
export const useSunatData = (
  firebaseUser,
  dateFilter,
  selectedClientIds,
  selectedCurrencies,
  selectedUserEmails,
  currentPage,
  sortBy,
  clients,
  users,
  viewMode = "detailed",
  refreshTrigger = 0
) => {
  const [ventas, setVentas] = useState([]);
  const [metrics, setMetrics] = useState({
    PEN: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 },
    USD: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 },
  });
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total_items: 0,
    total_pages: 0,
    has_next: false,
    has_previous: false,
  });
  const [loading, setLoading] = useState(false);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [errorData, setErrorData] = useState(null);

  // DEBUG: Rastrear cuando cambian los parámetros
  useEffect(() => {
    console.log("🔍 [useSunatData DEBUG] Parámetros cambiaron:", {
      selectedUserEmails_count: selectedUserEmails.length,
      selectedUserEmails,
      users_length: users.length,
      selectedClientIds_count: selectedClientIds.length,
      selectedCurrencies_count: selectedCurrencies.length,
    });
  }, [selectedUserEmails, users, selectedClientIds, selectedCurrencies]);

  // DEBUG: Rastrear SOLO cambios en selectedUserEmails
  useEffect(() => {
    console.log(
      "⚡ [useSunatData DEBUG] selectedUserEmails cambió DENTRO del hook:",
      {
        selectedUserEmails,
        length: selectedUserEmails.length,
      }
    );
  }, [selectedUserEmails]);

  // Función para fetch con autenticación (memorizada)
  const fetchWithAuth = async (url, options = {}) => {
    if (!firebaseUser) {
      console.error("fetchWithAuth: No hay usuario autenticado.");
      throw new Error("Usuario no autenticado");
    }
    try {
      const token = await firebaseUser.getIdToken();
      const headers = {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      };
      const response = await fetch(url, { ...options, headers });

      if (response.status === 401 || response.status === 403) {
        console.error("Error 401/403 - Forzando logout.");
        await signOut(auth);
        throw new Error(`Error ${response.status}: No autorizado.`);
      }
      if (!response.ok) {
        const errorBody = await response.text();
        console.error(`Error ${response.status} en ${url}:`, errorBody);
        throw new Error(`Error ${response.status} del servidor.`);
      }
      return response.json();
    } catch (error) {
      console.error("Error en fetchWithAuth:", error);
      if (error.message !== "Usuario no autenticado") {
        setErrorData(error.message);
      }
      throw error;
    }
  };

  // Calcular fechas desde/hasta basado en el filtro
  const { startDate, endDate, periodLabel, currentPeriod } = useMemo(() => {
    const today = new Date();
    let start = new Date(today);
    let end = new Date(today);
    let label = "";
    let periodo = "";

    switch (dateFilter.type) {
      case "5days":
        start.setDate(today.getDate() - 5);
        label = "Últimos 5 días";
        break;
      case "15days":
        start.setDate(today.getDate() - 15);
        label = "Últimos 15 días";
        break;
      case "30days":
        start.setDate(today.getDate() - 30);
        label = "Últimos 30 días";
        break;
      case "custom":
        start = new Date(dateFilter.start);
        end = new Date(dateFilter.end);
        label = `Del ${dateFilter.start} al ${dateFilter.end}`;
        break;
      case "thisMonth":
      default:
        start = new Date(today.getFullYear(), today.getMonth(), 1);
        end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        label = new Date(today.getFullYear(), today.getMonth())
          .toLocaleString("es-ES", { month: "long", year: "numeric" })
          .replace(/^\w/, (c) => c.toUpperCase());
        break;
    }

    periodo =
      start.getFullYear() + String(start.getMonth() + 1).padStart(2, "0");

    const formatDate = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    };

    return {
      startDate: formatDate(start),
      endDate: formatDate(end),
      periodLabel: label,
      currentPeriod: periodo,
    };
  }, [dateFilter]);

  // Fetch métricas optimizadas desde /api/metricas/resumen
  useEffect(() => {
    if (!firebaseUser || !startDate || !endDate) return;

    const fetchMetrics = async () => {
      setMetricsLoading(true);
      setErrorData(null);

      try {
        const params = new URLSearchParams({
          fecha_desde: startDate,
          fecha_hasta: endDate,
        });

        if (selectedCurrencies.length > 0) {
          selectedCurrencies.forEach((currency) =>
            params.append("moneda", currency)
          );
        }
        const shouldFilterClients =
          selectedClientIds.length > 0 &&
          (clients.length === 0 || selectedClientIds.length < clients.length);
        if (shouldFilterClients) {
          selectedClientIds.forEach((ruc) =>
            params.append("rucs_empresa", ruc)
          );
        }
        const totalUserOptions = users.length + 1;
        const shouldFilterUsers =
          selectedUserEmails.length > 0 &&
          (users.length === 0 || selectedUserEmails.length < totalUserOptions);
        if (shouldFilterUsers) {
          selectedUserEmails.forEach((email) =>
            params.append("usuario_emails", email)
          );
        }

        const url = `${API_BASE_URL}/api/metricas/resumen?${params.toString()}`;
        console.log("📊 [Metrics] Fetching from:", url);

        const data = await fetchWithAuth(url);

        let metricsData;
        if (data.PEN && data.USD) {
          metricsData = { PEN: data.PEN, USD: data.USD };
        } else {
          metricsData = {
            PEN: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 },
            USD: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 }
          };
        }
        setMetrics(metricsData);

      } catch (err) {
        console.error("❌ [Metrics] Error fetching metrics:", err);
        setMetrics({
          PEN: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 },
          USD: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 }
        });
      } finally {
        setMetricsLoading(false);
      }
    };

    fetchMetrics();
  }, [
    startDate, endDate, selectedClientIds, selectedCurrencies,
    selectedUserEmails, firebaseUser, clients.length, users.length, refreshTrigger
  ]);

  // Fetch ventas paginadas
  useEffect(() => {
    if (!firebaseUser || !startDate || !endDate) return;

    const fetchVentas = async () => {
      console.log("🚀 [useSunatData] Iniciando fetchVentas (Versión Original)...");
      try {
        setLoading(true);
        setError(null);

        const pageSize = viewMode === "grouped" ? 100 : 20;
        let url = `${API_BASE_URL}/api/ventas?page=${currentPage}&page_size=${pageSize}&fecha_desde=${startDate}&fecha_hasta=${endDate}&sort_by=${sortBy}`;

        if (selectedCurrencies.length === 1) {
          url += `&moneda=${selectedCurrencies[0]}`;
        }
        const shouldFilterClients =
          selectedClientIds.length > 0 &&
          (clients.length === 0 || selectedClientIds.length < clients.length);
        if (shouldFilterClients) {
          selectedClientIds.forEach((ruc) => {
            url += `&rucs_empresa=${ruc}`;
          });
        }
        const totalUserOptions = users.length + 1;
        const shouldFilterUsers =
          selectedUserEmails.length > 0 &&
          (users.length === 0 || selectedUserEmails.length < totalUserOptions);
        if (shouldFilterUsers) {
          selectedUserEmails.forEach((email) => {
            url += `&usuario_emails=${email}`;
          });
        }

        console.log("📊 [Ventas] URL final:", url);

        const data = await fetchWithAuth(url);

        const mappedItems = data.items.map(item => ({
          ...item,
          montoNeto: item.monto_neto,
          tieneNotaCredito: item.tiene_nota_credito,
          amount: item.monto_original,
          notaCreditoMonto: item.nota_credito_monto
        }));

        setVentas(mappedItems);
        setPagination(data.pagination);
      } catch (err) {
        console.error("Error fetching ventas:", err);
        setVentas([]);
        setPagination({ page: 1, page_size: 20, total_items: 0, total_pages: 0, has_next: false, has_previous: false });
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchVentas();
  }, [
    startDate, endDate, currentPage, selectedClientIds, clients.length,
    sortBy, selectedCurrencies, selectedUserEmails, firebaseUser, viewMode, users.length, refreshTrigger
  ]);

  return {
    ventas,
    metrics,
    metricsLoading,
    pagination,
    loading,
    error,
    errorData,
    startDate,
    endDate,
    periodLabel,
    currentPeriod,
  };
};
