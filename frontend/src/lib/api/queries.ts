import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiPost } from "./client";
import type {
  AccountBalancesResponse,
  AccountsResponse,
  AssetCategoryBreakdown,
  CashflowAssetSelection,
  CashflowResponse,
  DiagnosticsDbResponse,
  DiagnosticsEnvResponse,
  BudgetApplicabilityResponse,
  BudgetMonthViewResponse,
  BudgetsResponse,
  MetaResponse,
  NetWorthSummary,
  SyncResponse,
} from "./types";

export const apiKeys = {
  meta: ["meta"] as const,
  accounts: (dataVersion: number) => ["accounts", dataVersion] as const,
  diagnosticsEnv: (dataVersion: number) =>
    ["diagnostics-env", dataVersion] as const,
  diagnosticsDb: (dataVersion: number) =>
    ["diagnostics-db", dataVersion] as const,
  netWorth: (dataVersion: number, startDate: string, endDate: string) =>
    ["net-worth", dataVersion, startDate, endDate] as const,
  accountBalances: (dataVersion: number, endDate: string) =>
    ["account-balances", dataVersion, endDate] as const,
  assetCategoryBreakdown: (dataVersion: number, endDate: string, level: 1 | 2) =>
    ["asset-category-breakdown", dataVersion, endDate, level] as const,
  cashflowAssetSelection: (dataVersion: number, rootName: string) =>
    ["cashflow-asset-selection", dataVersion, rootName] as const,
  cashflow: (
    dataVersion: number,
    startDate: string,
    endDate: string,
    assetGuidsKey: string,
  ) => ["cashflow", dataVersion, startDate, endDate, assetGuidsKey] as const,
  budgets: (dataVersion: number) => ["budgets", dataVersion] as const,
  budgetApplicability: (
    dataVersion: number,
    budgetGuid: string,
    monthStart: string,
  ) => ["budget-applicability", dataVersion, budgetGuid, monthStart] as const,
  budgetMonthView: (
    dataVersion: number,
    budgetGuid: string,
    monthStart: string,
  ) => ["budget-month-view", dataVersion, budgetGuid, monthStart] as const,
};

function buildQuery(params: Record<string, string | number | undefined>): string {
  const urlParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && String(value).length > 0) {
      urlParams.set(key, String(value));
    }
  }
  const query = urlParams.toString();
  return query ? `?${query}` : "";
}

export function useMetaQuery() {
  return useQuery({
    queryKey: apiKeys.meta,
    queryFn: () => apiGet<MetaResponse>("/api/v1/meta"),
  });
}

export function useDataVersion(): number | undefined {
  const { data } = useMetaQuery();
  return data?.data_version;
}

export function useSyncAnalyticsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<SyncResponse>("/api/v1/sync/analytics"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: apiKeys.meta });
    },
  });
}

export function useAccountsQuery() {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.accounts(dataVersion ?? 0),
    queryFn: () => apiGet<AccountsResponse>("/api/v1/accounts"),
    enabled: dataVersion !== undefined,
  });
}

export function useDiagnosticsEnvQuery() {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.diagnosticsEnv(dataVersion ?? 0),
    queryFn: () => apiGet<DiagnosticsEnvResponse>("/api/v1/diagnostics/env"),
    enabled: dataVersion !== undefined,
  });
}

export function useDiagnosticsDbQuery() {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.diagnosticsDb(dataVersion ?? 0),
    queryFn: () => apiGet<DiagnosticsDbResponse>("/api/v1/diagnostics/db"),
    enabled: dataVersion !== undefined,
  });
}

export function useNetWorthQuery(startDate: string, endDate: string) {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.netWorth(dataVersion ?? 0, startDate, endDate),
    queryFn: () =>
      apiGet<NetWorthSummary>(
        `/api/v1/net-worth${buildQuery({ start_date: startDate, end_date: endDate, currency: "EUR" })}`,
      ),
    enabled: dataVersion !== undefined,
  });
}

export function useAccountBalancesQuery(endDate: string) {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.accountBalances(dataVersion ?? 0, endDate),
    queryFn: () =>
      apiGet<AccountBalancesResponse>(
        `/api/v1/account-balances${buildQuery({ end_date: endDate, currency: "EUR" })}`,
      ),
    enabled: dataVersion !== undefined,
  });
}

export function useAssetCategoryBreakdownQuery(endDate: string, level: 1 | 2) {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.assetCategoryBreakdown(dataVersion ?? 0, endDate, level),
    queryFn: () =>
      apiGet<AssetCategoryBreakdown>(
        `/api/v1/asset-category-breakdown${buildQuery({ end_date: endDate, currency: "EUR", level })}`,
      ),
    enabled: dataVersion !== undefined,
  });
}

export function useCashflowAssetSelectionQuery(assetRootName: string) {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.cashflowAssetSelection(dataVersion ?? 0, assetRootName),
    queryFn: () =>
      apiGet<CashflowAssetSelection>(
        `/api/v1/cashflow/asset-selection${buildQuery({ asset_root_name: assetRootName })}`,
      ),
    enabled: dataVersion !== undefined,
  });
}

export function useCashflowQuery(
  startDate: string,
  endDate: string,
  assetGuids: string[],
) {
  const dataVersion = useDataVersion();
  const assetGuidsKey = assetGuids.join(",");
  return useQuery({
    queryKey: apiKeys.cashflow(dataVersion ?? 0, startDate, endDate, assetGuidsKey),
    queryFn: () =>
      apiGet<CashflowResponse>(
        `/api/v1/cashflow${buildQuery({
          start_date: startDate,
          end_date: endDate,
          currency: "EUR",
          asset_guids: assetGuidsKey,
        })}`,
      ),
    enabled: dataVersion !== undefined && assetGuids.length > 0,
  });
}

export function useBudgetsQuery() {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.budgets(dataVersion ?? 0),
    queryFn: () => apiGet<BudgetsResponse>("/api/v1/budgets"),
    enabled: dataVersion !== undefined,
  });
}

export function useBudgetApplicabilityQuery(
  budgetGuid: string | undefined,
  monthStart: string,
) {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.budgetApplicability(dataVersion ?? 0, budgetGuid ?? "", monthStart),
    queryFn: () =>
      apiGet<BudgetApplicabilityResponse>(
        `/api/v1/budget/applicability${buildQuery({ budget_guid: budgetGuid, month_start: monthStart })}`,
      ),
    enabled: dataVersion !== undefined && Boolean(budgetGuid),
  });
}

export function useBudgetMonthViewQuery(
  budgetGuid: string | undefined,
  monthStart: string,
) {
  const dataVersion = useDataVersion();
  return useQuery({
    queryKey: apiKeys.budgetMonthView(dataVersion ?? 0, budgetGuid ?? "", monthStart),
    queryFn: () =>
      apiGet<BudgetMonthViewResponse>(
        `/api/v1/budget/month-view${buildQuery({ budget_guid: budgetGuid, month_start: monthStart })}`,
      ),
    enabled: dataVersion !== undefined && Boolean(budgetGuid),
  });
}
