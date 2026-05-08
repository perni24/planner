export interface Settings {
    id: number;
    language: string;
    theme: string;
    custom_background: string;
    custom_foreground: string;
    custom_card: string;
    custom_border: string;
    custom_hover: string;
    custom_hover_text: string;
}

export type CustomColors = {
  background: string;
  foreground: string;
  card: string;
  border: string;
  hover: string;
  hoverText: string;
};
