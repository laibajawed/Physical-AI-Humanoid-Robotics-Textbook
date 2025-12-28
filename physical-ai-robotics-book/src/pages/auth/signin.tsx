/**
 * Signin Page
 */

import React from "react";
import Layout from "@theme/Layout";
import SignInForm from "../../components/Auth/SignInForm";
import "../../components/Auth/auth-forms.css";

export default function SigninPage(): JSX.Element {
  return (
    <Layout
      title="Sign In"
      description="Sign in to access the Physical AI & Robotics textbook"
    >
      <main style={{ padding: "2rem 0" }}>
        <SignInForm />
      </main>
    </Layout>
  );
}
