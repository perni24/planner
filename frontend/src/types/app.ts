export interface AppVersion {
  version: string;
}

export interface AppUpdateStatus {
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  release_url: string;
  error: string | null;
}
