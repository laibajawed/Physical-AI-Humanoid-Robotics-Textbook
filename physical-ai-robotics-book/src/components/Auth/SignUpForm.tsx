/**
 * SignUpForm Component
 */

import React, { useState, FormEvent } from "react";
import { authClient } from "../../lib/auth-client";

interface SignUpFormProps {
  redirectUrl?: string;
  onSuccess?: () => void;
  onSignInClick?: () => void;
}

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

export function SignUpForm({
  redirectUrl = "/docs/introduction",
  onSuccess,
  onSignInClick,
}: SignUpFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = "Name is required";
    }

    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!isValidEmail(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const { data, error } = await authClient.signUp.email({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
        callbackURL: redirectUrl,
      });

      if (error) {
        let errorMessage = error.message || "An error occurred during sign up";
        
        if (error.code === "USER_ALREADY_EXISTS") {
          errorMessage = "An account with this email already exists";
        } else if (error.code === "WEAK_PASSWORD") {
          errorMessage = "Password is too weak. Please use at least 8 characters.";
        }

        setErrors({ general: errorMessage });
        return;
      }

      onSuccess?.();
      
      if (typeof window !== "undefined") {
        window.location.href = redirectUrl;
      }
    } catch (err) {
      console.error("Sign up error:", err);
      setErrors({
        general: "An unexpected error occurred. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <h2 className="auth-form-title">Create an Account</h2>
      <p className="auth-form-subtitle">
        Sign up to access the Physical AI & Robotics textbook
      </p>

      {errors.general && (
        <div className="auth-form-error-banner" role="alert">
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="auth-form-field">
          <label htmlFor="name" className="auth-form-label">Name</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={`auth-form-input ${errors.name ? "auth-form-input-error" : ""}`}
            placeholder="John Doe"
            disabled={isLoading}
            autoComplete="name"
          />
          {errors.name && <span className="auth-form-field-error">{errors.name}</span>}
        </div>

        <div className="auth-form-field">
          <label htmlFor="email" className="auth-form-label">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={`auth-form-input ${errors.email ? "auth-form-input-error" : ""}`}
            placeholder="you@example.com"
            disabled={isLoading}
            autoComplete="email"
          />
          {errors.email && <span className="auth-form-field-error">{errors.email}</span>}
        </div>

        <div className="auth-form-field">
          <label htmlFor="password" className="auth-form-label">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={`auth-form-input ${errors.password ? "auth-form-input-error" : ""}`}
            placeholder="At least 8 characters"
            disabled={isLoading}
            autoComplete="new-password"
          />
          {errors.password && <span className="auth-form-field-error">{errors.password}</span>}
        </div>

        <div className="auth-form-field">
          <label htmlFor="confirmPassword" className="auth-form-label">Confirm Password</label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={`auth-form-input ${errors.confirmPassword ? "auth-form-input-error" : ""}`}
            placeholder="Re-enter your password"
            disabled={isLoading}
            autoComplete="new-password"
          />
          {errors.confirmPassword && <span className="auth-form-field-error">{errors.confirmPassword}</span>}
        </div>

        <button type="submit" className="auth-form-submit" disabled={isLoading}>
          {isLoading ? "Creating account..." : "Create Account"}
        </button>
      </form>

      <p className="auth-form-switch">
        Already have an account?{" "}
        {onSignInClick ? (
          <button type="button" onClick={onSignInClick} className="auth-form-link-button">
            Sign in
          </button>
        ) : (
          <a href="/auth/signin" className="auth-form-link">Sign in</a>
        )}
      </p>
    </div>
  );
}

export default SignUpForm;
