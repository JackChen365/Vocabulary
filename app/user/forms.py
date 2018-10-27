from django import forms


class RegisterForm(forms.Form):
    username = forms.CharField(label='Username', min_length=2, required=True, max_length=12, error_messages={
        'required': '用户名不能为空',
        'max_length': '最大长度不得超过12个字符',
        'min_length': '最小长度不得少于2个字符'
    })
    email = forms.EmailField(label='Email', required=True, error_messages={
        'required': '用户邮箱不能为空',
        'invalid': '邮箱格式不正确',
    })
    password1 = forms.CharField(label='Password', min_length=2, max_length=12, required=True,
                                widget=forms.PasswordInput,
                                error_messages={
                                    'required': '用户名密码不能为空',
                                    'max_length': '最大长度不得超过12个字符',
                                    'min_length': '最小长度不得少于2个字符'
                                })
    password2 = forms.CharField(label='Verify ', min_length=2, max_length=12, required=True,
                                widget=forms.PasswordInput,
                                error_messages={
                                    'required': '用户名密码不能为空',
                                    'max_length': '最大长度不得超过12个字符',
                                    'min_length': '最小长度不得少于2个字符'
                                })