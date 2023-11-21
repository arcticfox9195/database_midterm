const loginText = document.querySelector(".title-text .login");
      const loginForm = document.querySelector("form.login");
      const loginLb = document.querySelector("label.login");
      const signupLb = document.querySelector("label.signup");
      const signupLink = document.querySelector("form .signup-link a");
      signupLb.onclick = (()=>{
        loginForm.style.marginLeft = "-50%";
        loginText.style.marginLeft = "-50%";
      });
      loginLb.onclick = (()=>{
        loginForm.style.marginLeft = "0%";
        loginText.style.marginLeft = "0%";
      });
      signupLink.onclick = (()=>{
        signupLb.click();
        return false;
      });

      

      
