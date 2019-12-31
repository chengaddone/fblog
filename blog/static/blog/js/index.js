$(function() {

    // 打开登录框
    $('.login_btn').click(function () {
        $('.login_form_con').show();
    });

    // 点击关闭按钮关闭登录框或者注册框
    $('.shutoff').click(function () {
        $(this).closest('form').hide();
    });

    // 隐藏错误
    $(".login_form #mobile").focus(function () {
        $("#login-mobile-err").hide();
    });
    $(".login_form #password").focus(function () {
        $("#login-password-err").hide();
    });

    $(".register_form #mobile").focus(function () {
        $("#register-mobile-err").hide();
    });
    $(".register_form #imagecode").focus(function () {
        $("#register-image-code-err").hide();
    });
    $(".register_form #smscode").focus(function () {
        $("#register-sms-code-err").hide();
    });
    $(".register_form #password").focus(function () {
        $("#register-password-err").hide();
    });

    $('.form_group').on('click',function(){
        $(this).children('input').focus();
    });

    $('.form_group input').on('focusin',function(){
        $(this).siblings('.input_tip').animate({'top':-5,'font-size':12},'fast');
        $(this).parent().addClass('hotline');
        $(this).nextAll('#register-mobile-err').hide()
    });

	// 输入框失去焦点，如果输入框为空，则提示文字下移
	$('.form_group input').on('blur focusout',function(){
		$(this).parent().removeClass('hotline');
		var val = $(this).val();
		if(val=='')
		{
			$(this).siblings('.input_tip').animate({'top':22,'font-size':14},'fast');
		}
	});


    // 打开注册框
    $('.register_btn').click(function () {
        $('.register_form_con').show();
        generateImageCode()
    });


    // 登录框和注册框切换
    $('.to_register').click(function () {
        $('.login_form_con').hide();
        $('.register_form_con').show();
        generateImageCode()
    });

    // 登录框和注册框切换
    $('.to_login').click(function () {
        $('.login_form_con').show();
        $('.register_form_con').hide();
    });

    // 注册按钮点击
    $(".register_form_con").submit(function (e) {
        // 阻止默认提交操作
        e.preventDefault();
		// 取到用户输入的内容
        var e_mail = $("#register_mobile").val();
        var email_code = $("#smscode").val();
        var password = $("#register_password").val();

		if (!e_mail) {
            $("#register-mobile-err").show();
            return;
        }
        if (!email_code) {
            $("#register-sms-code-err").show();
            return;
        }
        if (!password) {
            $("#register-password-err").html("请填写密码!");
            $("#register-password-err").show();
            return;
        }
		if (password.length < 6) {
            $("#register-password-err").html("密码长度不能少于6位");
            $("#register-password-err").show();
            return;
        }

		var params = {
		    "e_mail": e_mail,
            "email_code": email_code,
            "password": password
        };
		// TODO: 发送请求
        $.ajax({
            url: "/auth/register",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(params),
            headers:{'X-CSRFToken':getCookie('csrf_token')},
            success: function (resp) {
                if (resp.errno == 0){
                    //注册成功
                    location.reload();
                }
                else {
                    //注册失败
                    alert(resp.errmsg);
                    $("#register-password-err").html(resp.errmsg);
                    $("#register-password-err").show()
                }
            }
        });
    });

    // 登录表单提交
    $(".login_form_con").submit(function (e) {
        e.preventDefault();
        var e_mail = $(".login_form #mobile").val();
        var password = $(".login_form #password").val()

        if (!e_mail) {
            $("#login-mobile-err").show();
            return;
        }

        if (!password) {
            $("#login-password-err").show();
            return;
        }

        // 发起登录请求
        var params = {
            "e_mail": e_mail,
            "password": password
        };

        $.ajax({
            url:'/auth/login',
            type:'post',
            data:JSON.stringify(params),
            contentType:'application/json',
            headers:{'X-CSRFToken':getCookie('csrf_token')},
            success: function (resp) {
                if (resp.errno == 0){
                    //登录成功
                    location.reload();
                }else{
                    //登录失败
                    $("#login-password-err").html(resp.errmsg);
                    $("#login-password-err").show();
                }
            }
        });
    });

});

var imageCodeId = "";

// 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
function generateImageCode() {
    // 浏览器要发起图片验证请求格式为/image_code?imageCodeId=xxx
    imageCodeId = generateUUID();  // 生成当前唯一的编码
    // 1.生成向后台请求的url
    var url = "/auth/image_code?imageCodeId=" + imageCodeId;
    // 2.给指定img标签设置src
    $(".get_pic_code").attr("src", url);
}

function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

//发送邮箱验证码
function sendEmailCode() {
    // 校验参数，保证输入框有数据填写
    $(".get_code").removeAttr("onclick");
    var e_mail = $("#register_mobile").val();
    if (!e_mail) {
        $("#register-mobile-err").html("请填写电子邮箱！");
        $("#register-mobile-err").show();
        $(".get_code").attr("onclick", "sendEmailCode();");
        return;
    }
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#register-image-code-err").html("请填写验证码！");
        $("#register-image-code-err").show();
        $(".get_code").attr("onclick", "sendEmailCode();");
        return;
    }

    // TODO 发送邮箱验证码
    var params = {
		    "e_mail": e_mail,
            "image_code_id": imageCodeId,
            "image_code": imageCode
        };

    // 发起注册请求
    $.ajax({
        url:'/auth/email_code',//请求地址
        type:'post',
        data:JSON.stringify(params),
        contentType:'application/json',
        headers:{'X-CSRFToken':getCookie('csrf_token')},
        success: function (resp) {
            //判断是否请求成功
            if(resp.errno == '0'){
                //定义倒计时时间
                var num = 120;
                //创建定时器
                var t = setInterval(function () {
                    //判断是否倒计时结束
                    if(num == 1){
                        //清除定时器
                        clearInterval(t)
                        //设置标签点击事件,并设置内容
                        $(".get_code").attr("onclick",'sendEmailCode()');
                        $(".get_code").html('点击获取验证码');
                    }else{
                        //设置秒数
                        num -= 1;
                        $('.get_code').html(num + '秒后可再次发送');
                    }
                },1000);//一秒走一次
            }else if(resp.errno == '4103'){//邮箱校验失败
                $("#register-mobile-err").html("请填写正确的邮箱信息");
                $("#register-mobile-err").show();
                // 重新设置点击事件,更新图片验证码
                $(".get_code").attr("onclick",'sendEmailCode()');
            }else if(resp.errno == '4002'){// 图片验证码已过期
                $("#register-image-code-err").html("图片验证码已过期！");
                $("#register-image-code-err").show();
                $(".get_code").attr("onclick",'sendEmailCode()');
                generateImageCode();
            }else if(resp.errno == '4004'){// 图片验证码输入错误
                $("#register-image-code-err").html("图片验证码输入错误！");
                $("#register-image-code-err").show();
                $(".get_code").attr("onclick",'sendEmailCode()');
            }
            else{// 其他错误
                // 重新设置点击事件,更新图片验证码
                alert("系统错误，请稍后再试");
                $(".get_code").attr("onclick",'sendEmailCode()');
                generateImageCode();
            }
        }
    });
}

//退出登录
function logout() {
    $.get('/auth/logout', function (resp) {
        location.reload();
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
