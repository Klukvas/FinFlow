import { useCallback, useState } from "react";
import { validateEmail } from "../utils";

interface UseAuthFormProps<T> {
  initialValues: T;
  onSubmit: (data: T) => Promise<void>;
  validateEmail?: boolean;
}

interface UseAuthFormReturn<T> {
  formData: T;
  setFormData: React.Dispatch<React.SetStateAction<T>>;
  error: string;
  isLoading: boolean;
  handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  setError: React.Dispatch<React.SetStateAction<string>>;
  reset: () => void;
}

export function useAuthForm<T extends Record<string, any>>({
  initialValues,
  onSubmit,
  validateEmail: shouldValidateEmail = true,
}: UseAuthFormProps<T>): UseAuthFormReturn<T> {
  const [formData, setFormData] = useState<T>(initialValues);
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }, []);

  const reset = useCallback(() => {
    setFormData(initialValues);
    setError("");
    setIsLoading(false);
  }, [initialValues]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    if (shouldValidateEmail && formData.email && !validateEmail(formData.email)) {
      setError("Введите корректный email.");
      setIsLoading(false);
      return;
    }

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission error:', error);
      setError("Что-то пошло не так. Попробуйте еще раз.");
    } finally {
      setIsLoading(false);
    }
  }, [formData, onSubmit, shouldValidateEmail]);

  return { 
    formData, 
    setFormData, 
    error, 
    isLoading, 
    handleChange, 
    handleSubmit, 
    setError,
    reset
  };
}