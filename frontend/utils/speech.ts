// Funciones para manejar el reconocimiento de voz con Google Speech-to-Text a través del backend

/**
 * Clase para manejar la grabación de audio
 */
export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private isRecording: boolean = false;

  /**
   * Iniciar la grabación de audio
   */
  async startRecording(): Promise<void> {
    if (this.isRecording) return;

    try {
      // Solicitar permisos de micrófono
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Configurar MediaRecorder
      this.mediaRecorder = new MediaRecorder(this.stream);
      this.audioChunks = [];
      
      // Manejar fragmentos de audio
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };
      
      // Iniciar grabación
      this.mediaRecorder.start();
      this.isRecording = true;
      
      console.log('Grabación de audio iniciada');
    } catch (error) {
      console.error('Error al iniciar la grabación:', error);
      throw new Error(`Error al iniciar la grabación: ${error}`);
    }
  }

  /**
   * Detener la grabación y devolver el blob de audio
   */
  stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || !this.isRecording) {
        reject(new Error('No hay grabación activa'));
        return;
      }

      // Manejar finalización de grabación
      this.mediaRecorder.onstop = () => {
        // Crear Blob con los fragmentos de audio
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        // Detener el stream
        if (this.stream) {
          this.stream.getTracks().forEach(track => track.stop());
          this.stream = null;
        }
        
        this.isRecording = false;
        this.mediaRecorder = null;
        
        console.log('Grabación de audio detenida');
        resolve(audioBlob);
      };

      // Detener grabación
      this.mediaRecorder.stop();
    });
  }

  /**
   * Verificar si está grabando
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }
}

/**
 * Función para enviar audio al backend para reconocimiento de voz
 */
export const recognizeSpeech = async (audioBlob: Blob): Promise<string | any> => {
  // Crear FormData para enviar el archivo
  const formData = new FormData();
  formData.append('audio', audioBlob);

  try {
    // Determinar URL base - Corrección para apuntar correctamente al puerto del backend
    const baseUrl = process.server 
      ? '' 
      : window.location.origin.includes('localhost') 
        ? 'http://localhost:5000'
        : window.location.origin;
    
    // Enviar solicitud al backend
    const response = await fetch(`${baseUrl}/api/speech-recognition`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Error en el reconocimiento de voz');
    }

    const data = await response.json();
    
    // Verificar si hay resultados
    if (!data.results || data.results.length === 0) {
      return '';
    }

    // NUEVO: Verificar si hay un error de duplicación
    if (data.results[0].error && data.results[0].isDuplicate) {
      return {
        transcript: data.results[0].transcript || '',
        error: true,
        isDuplicate: true,
        message: data.results[0].message || `Número duplicado detectado.`
      };
    }

    // Devolver la transcripción con mayor confianza
    return data.results[0].transcript;
  } catch (error) {
    console.error('Error en el reconocimiento de voz:', error);
    throw error;
  }
}; 