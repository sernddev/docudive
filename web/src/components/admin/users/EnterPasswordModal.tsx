"use client";

import { withFormik, FormikProps, FormikErrors, Form, Field } from "formik";
import { Button } from "@tremor/react";

interface FormProps {
  onSuccess: (res:Response) => void;
  onFailure: (res: Response) => void;
}

interface FormValues {
  password: string;
}

const verifyPassword = async (url: string, { arg }: { arg: string }) => {
  return await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ password: arg }),
  });
};

const EnterPasswordFormRenderer = ({
                                     touched,
                                     errors,
                                     isSubmitting,
                                   }: FormikProps<FormValues>) => (
  <Form>
    <div className="flex flex-col gap-y-4">
      <Field
        id="password"
        name="password"
        type="password"
        placeholder="Enter Password"
        className="p-4"
      />
      {touched.password && errors.password && (
        <div className="text-error text-sm">{errors.password}</div>
      )}
      <Button
        className="mx-auto"
        color="red"
        size="md"
        type="submit"
        disabled={isSubmitting}
      >
        Submit
      </Button>
    </div>
  </Form>
);

const EnterPasswordForm = withFormik<FormProps, FormValues>({
  mapPropsToValues: () => {
    return {
      password: "",
    };
  },
  validate: (values: FormValues): FormikErrors<FormValues> => {
    if (!values.password.trim()) {
      return { password: "Password is required" };
    }
    return {};
  },
  handleSubmit: async (values: FormValues, formikBag) => {
    await verifyPassword("/api/manage/load_ldap_users", { arg: values.password }).then((res) => {
    //await verifyPassword("/api/manage/ldap_users", { arg: values.password }).then((res) => {
      if (res.ok) {
        formikBag.props.onSuccess(res);
      } else {
        formikBag.props.onFailure(res);
      }
    });
  },
})(EnterPasswordFormRenderer);

const EnterPasswordModal = ({ onSuccess, onFailure }: FormProps) => {
  return <EnterPasswordForm onSuccess={onSuccess} onFailure={onFailure} />;
};

export default EnterPasswordModal;
