function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pic_info").submit(function (e) {
        e.preventDefault();

        //TODO 上传头像
        $(this).ajaxSubmit({
            url: "/admin/admin_head_pic",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    $(".now_user_pic").attr("src", resp.data.avatar_url);
                    $(".user_info>img", parent.document).attr("src", resp.data.avatar_url);
                }else {
                    alert(resp.errmsg);
                }
            }
        });
    });

    $("#reset").click(function () {
        $.ajax({
            url: "/admin/reset_head_pic",
            type: "post",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    $(".now_user_pic").attr("src", resp.data.avatar_url);
                    $(".user_info>img", parent.document).attr("src", resp.data.avatar_url);
                }else {
                    alert(resp.errmsg);
                }
            }
        })
    })
});