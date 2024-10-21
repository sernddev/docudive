"use client";

import { TextFormField } from "@/components/admin/connectors/Field";
import { usePopup } from "@/components/admin/connectors/Popup";
import { basicLogin, basicSignup } from "@/lib/user";
import { Button } from "@tremor/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/navigation";
import * as Yup from "yup";
import { requestEmailVerification } from "../lib";
import { useState } from "react";
import { Spinner } from "@/components/Spinner";

export function EmailPasswordForm({
  isSignup = false,
  shouldVerify,
}: {
  isSignup?: boolean;
  shouldVerify?: boolean;
}) {
  const router = useRouter();
  const { popup, setPopup } = usePopup();
  const [isWorking, setIsWorking] = useState(false);

  return (
    <>
      {isWorking && <Spinner />}
      {popup}
      <Formik
        initialValues={{
          loginid: "",
          password: "",
          name: ""
        }}
        validationSchema={Yup.object().shape({
          loginid: Yup.string().required(),
          password: Yup.string().required(),
        })}
        onSubmit={async (values) => {
          if (isSignup) {
            // login is fast, no need to show a spinner
            setIsWorking(true);
            const response = await basicSignup(values.loginid, values.password);

            if (!response.ok) {
              const errorDetail = (await response.json()).detail;

              let errorMsg = "Unknown error";
              if (errorDetail === "REGISTER_USER_ALREADY_EXISTS") {
                errorMsg =
                  "An account already exists with the specified email.";
              }
              setPopup({
                type: "error",
                message: `Failed to sign up - ${errorMsg}`,
              });
              setTimeout(() => {
                window.location.reload();
              }, 2000);
              return;
            }
          }

          const loginResponse = await basicLogin(values.loginid, values.password);
          if (loginResponse.ok) {
            if (isSignup && shouldVerify) {
              //await requestEmailVerification(values.email);
              router.push("/auth/waiting-on-verification");
            } else {
              
              if (isSignup)
              {
                const response = await fetch("/api/settings/user_info", {
                method: "PUT",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  key: values.loginid,
                  value: values.name,
                  }),
                });
              }
              router.push("/");
              window.location.reload();
            }
          } else {
            setIsWorking(false);
            const errorDetail = (await loginResponse.json()).detail;

            let errorMsg = "Unknown error";
            if (errorDetail != null && errorDetail != "") {
              errorMsg = errorDetail;
            }
            if (errorDetail === "LOGIN_BAD_CREDENTIALS") {
              errorMsg = "Invalid login Id or password";
            }
            setPopup({
              type: "error",
              message: `Failed to login - ${errorMsg}`,
            });
          }
        }}
      >
        {({ isSubmitting, values }) => (
          <Form>            
            {
              isSignup? <TextFormField
                name="name"
                label="Name"    
                placeholder="Your Name"
              />: ''
            }
            <TextFormField
              name="loginid"
              label="Login Id"
              placeholder="enter your login id"
            />
            <TextFormField
              name="password"
              label="Password"
              type="password"
              placeholder="**************"
            />
            <div className="flex">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="mx-auto w-full"
              >
                {isSignup ? "Sign Up" : "Log In"}
              </Button>
            </div>
          </Form>
        )}
      </Formik>
    </>
  );
}
