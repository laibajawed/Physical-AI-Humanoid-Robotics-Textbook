/**
 * SignInForm Component
 */

import React, { useState, FormEvent } from "react";
import { authClient } from "../../lib/auth-client";

interface SignInFormProps {
  redirectUrl?: string;
  onSuccess?: () => void;
  onSignUpClick?: () => void;
}

interface FormErrors {
  email?: string;
  password?: string;
  general?: string;
}

export function SignInForm({
  redirectUrl,
  onSuccess,
  onSignUpClick,
}: SignInFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const getRedirectUrl = (): string => {
    if (redirectUrl) return redirectUrl;
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      return params.get("redirect") || "/docs/introduction";
    }
    return "/docs/introduction";
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!email.trim()) {
      newErrors.email = "Email is required";
    }

    if (!password) {
      newErrors.password = "Password is required";
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
      const { data, error } = await authClient.signIn.email({
        email: email.trim().toLowerCase(),
        password,
        rememberMe,
        callbackURL: getRedirectUrl(),
      });

      if (error) {
        setErrors({ general: "Invalid email or password" });
        return;
      }

      onSuccess?.();
      
      if (typeof window !== "undefined") {
        window.location.href = getRedirectUrl();
      }
    } catch (err) {
      console.error("Sign in error:", err);
      setErrors({
        general: "An unexpected error occurred. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <h2 className="auth-form-title">Welcome Back</h2>
      <p className="auth-form-subtitle">
        Sign in to access the Physical AI & Robotics textbook
      </p>

      {errors.general && (
        <div className="auth-form-error-banner" role="alert">
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="auth-form-field">
          <label htmlFor="email" className="auth-form-label">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={"auth-form-input " + (errors.email ? "auth-form-input-error" : "")}
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
            className={"auth-form-input " + (errors.password ? "auth-form-input-error" : "")}
            placeholder="Your password"
            disabled={isLoading}
            autoComplete="current-password"
          />
          {errors.password && <span className="auth-form-field-error">{errors.password}</span>}
        </div>

        <div className="auth-form-checkbox">
          <label className="auth-form-checkbox-label">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="auth-form-checkbox-input"
              disabled={isLoading}
            />
            <span>Remember me for 30 days</span>
          </label>
        </div>

        <button type="submit" className="auth-form-submit" disabled={isLoading}>
          {isLoading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <p className="auth-form-switch">
        Do not have an account?{" "}
        {onSignUpClick ? (
          <button type="button" onClick={onSignUpClick} className="auth-form-link-button">
            Sign up
          </button>
        ) : (
          <a href="/auth/signup" className="auth-form-link">Sign up</a>
        )}
      </p>
    </div>
  );
}

export default SignInForm;
