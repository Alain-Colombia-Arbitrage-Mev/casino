// Tipos para los números de la ruleta
export interface RouletteNumber {
  id: number;
  number: number;
  timestamp: string;
  color: string; // 'red', 'black', 'green'
}

// Tipos para el historial de la ruleta
export interface RouletteHistory {
  id: number;
  numbers: string; // números separados por coma
  timestamp: string;
}

// Tipo para los mensajes del chat
export interface ChatMessage {
  id: number;
  message: string;
  sender: 'user' | 'bot';
  timestamp: string;
  isWinning?: boolean;
  numbersGenerated?: number[];
  isDuplicate?: boolean;
  duplicateNumber?: number;
  allowOverride?: boolean;
}

// Tipos para las estadísticas
export interface RouletteStats {
  hotNumbers: number[];
  coldNumbers: number[];
  redVsBlack: {
    red: number;
    black: number;
  };
  oddVsEven: {
    odd: number;
    even: number;
  };
  columns: {
    c1: number;
    c2: number;
    c3: number;
  };
  dozens: {
    d1: number;
    d2: number;
    d3: number;
  };
  lastNumbers: number[];
}

// Definiciones para Web Speech API
declare global {
  interface Window {
    webkitSpeechRecognition: any;
    SpeechRecognition: any;
  }
} 