export type MetaResponse = {
  data_version: number;
  read_mode: "tables" | "views";
  backend: "sqlalchemy" | "analytics" | "piecash";
};

export type SyncResponse = {
  accounts_count: number;
  commodities_count: number;
  splits_count: number;
  transactions_count: number;
  prices_count: number;
  data_version: number;
};

export type AccountDTO = {
  guid: string;
  name: string;
  account_type: string;
  commodity_guid: string | null;
  parent_guid: string | null;
};

export type AccountsResponse = {
  accounts: AccountDTO[];
};

export type NetWorthSummary = {
  asset_total: string;
  liability_total: string;
  net_worth: string;
  currency_code: string;
};

export type AccountBalanceDTO = {
  guid: string;
  name: string;
  account_type: string;
  parent_guid: string | null;
  balance: string | null;
  currency_code: string;
};

export type AccountBalancesResponse = {
  balances: AccountBalanceDTO[];
};

export type AssetCategoryAmount = {
  category: string;
  amount: string;
  parent_category: string | null;
};

export type AssetCategoryBreakdown = {
  currency_code: string;
  categories: AssetCategoryAmount[];
};

export type CashflowAssetOption = {
  guid: string;
  display_name: string;
};

export type CashflowAssetSelection = {
  asset_root_name: string;
  options: CashflowAssetOption[];
  default_selected_guids: string[];
};

export type CashflowItem = {
  account_full_name: string;
  amount: string;
  top_parent_name: string | null;
};

export type CashflowResponse = {
  summary: {
    total_in: string;
    total_out: string;
    currency_code: string;
    difference: string;
  };
  incoming: CashflowItem[];
  outgoing: CashflowItem[];
};

export type DiagnosticsEnvResponse = {
  env: {
    ANALYTICS_DB_URL_present: boolean;
    GNUCASH_DB_URL_present: boolean;
    ANALYTICS_READ_MODE: string;
  };
};

export type DiagnosticsDbResponse = {
  analytics_db_ok: boolean;
  views: Array<{ name: string; present: boolean }>;
  error?: {
    code: string;
    message: string;
  };
};

export type BudgetDTO = {
  guid: string;
  name: string;
  num_periods: number;
};

export type BudgetsResponse = {
  budgets: BudgetDTO[];
};

export type BudgetApplicabilityResponse = {
  applicable: boolean;
  reason: "out_of_range" | "no_targets" | "data_unavailable" | null;
};

export type BudgetMonthViewResponse = {
  summary: {
    total_budget: string;
    total_actual: string;
    total_remaining: string;
    total_over: string;
    status_label: "No budget" | "On track" | "Close" | "Over";
  };
  node_results: Array<{
    node_guid: string;
    node_path: string;
    budget: string;
    actual: string;
    remaining: string;
    over: string;
    status_label: "No budget" | "On track" | "Close" | "Over";
    no_budget: boolean;
  }>;
};
