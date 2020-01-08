function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){
    $(".review_pass").click(function () {
        var commentId = $(this).attr("data-commentid");

        params = {
            "action": "agree",
            "commentId": commentId
        };

        $.ajax({
            url: "/admin/comment_audit",
            method: "post",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            data: JSON.stringify(params),
            contentType: "application/json",
            success: function (resp) {
                if (resp.errno == "0"){
                    alert("审核通过");
                    //刷新当前页面
                    location.reload();
                }else{
                    alert(resp.errmsg);
                }
            }
        })
    });

    $(".review_no_pass").click(function () {
        var commentId = $(this).attr("data-commentid");

        params = {
            "action": "reject",
            "commentId": commentId
        };

        $.ajax({
            url: "/admin/comment_audit",
            method: "post",
            headers: {"X-CSRFToken": getCookie("csrf_token")},
            data: JSON.stringify(params),
            contentType: "application/json",
            success: function (resp) {
                if (resp.errno == "0"){
                    alert("操作成功");
                    //刷新当前页面
                    location.reload();
                }else{
                    alert(resp.errmsg);
                }
            }
        })
    })
});