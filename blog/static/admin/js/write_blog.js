function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function () {
    $(".write_blog").submit(function (e) {
        //屏蔽默认的表单提交
        e.preventDefault();

        $(this).ajaxSubmit({
            //是为了处理富文本(可以有颜色,大小)
            beforeSubmit: function (request) {
                // 在提交之前，对参数进行处理
                for(var i=0; i<request.length; i++) {
                    var item = request[i];
                    if (item["name"] == "content") {
                        item["value"] = tinyMCE.activeEditor.getContent()
                    }
                }
            },
            url: "/admin/write_blog",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 选中索引为6的左边单菜单
                    alert("发布成功！")
                }else {
                    alert(resp.errmsg)
                }
            }
        });
    })
});