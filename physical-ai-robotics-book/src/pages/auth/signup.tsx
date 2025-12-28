/**
 * Signup Page
 */

import React from "react";
import Layout from "@theme/Layout";
import SignUpForm from "../../components/Auth/SignUpForm";
import "../../components/Auth/auth-forms.css";

export default function SignupPage(): JSX.Element {
  return (
    <Layout
      title="Sign Up"
      description="Create an account to access the Physical AI & Robotics textbook"
    >
      <main style={{ padding: "2rem 0" }}>
        <SignUpForm />
      </main>
    </Layout>
  );
}
